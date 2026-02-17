from __future__ import annotations

import asyncio
import signal
from datetime import timezone

from app.clickhouse.client import close_clickhouse_client, get_clickhouse_client
from app.config import get_settings
from app.db.session import close_pg_pool, init_pg_pool
from app.kafka.dlq import DlqPublisher
from app.kafka.producer import build_consumer, log_consumer_error
from app.kafka.serde import get_serde
from app.kafka.worker_metrics import WorkerAutoscalingMetrics
from app.logging import get_logger, setup_logging
from app.metrics import CLICKHOUSE_INSERT_SECONDS, CONSUMER_PROCESSING_SECONDS
from app.tracing import extract_context_from_kafka_headers, get_tracer, setup_tracing
from app.utils.idempotency import mark_processed

logger = get_logger(__name__)
tracer = get_tracer(__name__)


async def run() -> None:
    setup_logging()
    setup_tracing("clickhouse-writer")

    settings = get_settings()
    serde = get_serde()
    pool = await init_pg_pool()
    consumer = build_consumer(
        group_id=settings.clickhouse_writer_group_id,
        topics=[settings.ledger_entry_batches_topic],
        client_suffix="clickhouse-writer",
    )
    dlq = DlqPublisher(stage="clickhouse-writer")
    autoscaling = WorkerAutoscalingMetrics(worker_name="clickhouse-writer")
    running = True

    def stop_handler(*_: object) -> None:
        nonlocal running
        running = False

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop_handler)

    ch = get_clickhouse_client()

    try:
        while running:
            msg = consumer.poll(1.0)
            if msg is None:
                await asyncio.sleep(0)
                continue
            if msg.error():
                logger.error("kafka_consume_error", extra={"error": str(msg.error())})
                continue

            payload_dict: dict | None = None
            schema_id: int | None = None
            correlation_id = ""
            key = (msg.key() or b"").decode("utf-8", errors="ignore")
            parent_ctx = extract_context_from_kafka_headers(msg.headers())

            try:
                with tracer.start_as_current_span(
                    "consume.ledger_entry_batches.clickhouse",
                    context=parent_ctx,
                ):
                    timer = CONSUMER_PROCESSING_SECONDS.labels(
                        consumer="clickhouse-writer",
                        topic=msg.topic(),
                    ).time()
                    with timer:
                        deserialized = serde.deserialize_ledger_entry_batch(msg.value())
                        schema_id = deserialized.schema_id
                        payload_dict = serde.ledger_batch_to_dict(deserialized.message)
                        correlation_id = payload_dict["correlation_id"]

                        async with pool.acquire() as conn:
                            async with conn.transaction():
                                first_time = await mark_processed(
                                    conn,
                                    "clickhouse-writer",
                                    payload_dict["batch_id"],
                                )
                                if not first_time:
                                    consumer.commit(msg)
                                    continue

                        rows = []
                        for entry in payload_dict["entries"]:
                            rows.append(
                                [
                                    entry["occurred_at"].astimezone(timezone.utc),
                                    payload_dict["workspace_id"],
                                    payload_dict["batch_id"],
                                    payload_dict["tx_id"],
                                    payload_dict["event_id"],
                                    payload_dict["correlation_id"],
                                    entry["account_id"],
                                    entry["side"],
                                    entry["asset"],
                                    str(entry["amount"]),
                                ]
                            )

                        with CLICKHOUSE_INSERT_SECONDS.time():
                            with tracer.start_as_current_span("clickhouse.insert_ledger_entries") as span:
                                span.set_attribute("rows", len(rows))
                                ch.insert(
                                    "polyphony.ledger_entries_raw",
                                    rows,
                                    column_names=[
                                        "occurred_at",
                                        "workspace_id",
                                        "batch_id",
                                        "tx_id",
                                        "event_id",
                                        "correlation_id",
                                        "account_id",
                                        "side",
                                        "asset",
                                        "amount",
                                    ],
                                )

                        autoscaling.observe_processed(
                            consumer=consumer,
                            topic=msg.topic(),
                            partition=msg.partition(),
                            offset=msg.offset(),
                        )
                        consumer.commit(msg)
            except Exception as exc:
                log_consumer_error("clickhouse-writer", exc)
                dlq.publish(
                    topic=settings.dlq_clickhouse_topic,
                    source_topic=msg.topic(),
                    key=key,
                    error=exc,
                    correlation_id=correlation_id,
                    schema_id=schema_id,
                    decoded_payload=payload_dict,
                    raw_payload=msg.value(),
                )
                consumer.commit(msg)

    finally:
        consumer.close()
        await close_pg_pool()
        close_clickhouse_client()


if __name__ == "__main__":
    asyncio.run(run())
