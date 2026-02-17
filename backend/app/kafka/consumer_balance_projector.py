from __future__ import annotations

import asyncio
import json
import signal

from app.config import get_settings
from app.db.session import close_pg_pool, init_pg_pool
from app.kafka.dlq import DlqPublisher
from app.kafka.producer import KafkaProducer, build_consumer, log_consumer_error
from app.kafka.serde import get_serde
from app.kafka.worker_metrics import WorkerAutoscalingMetrics
from app.logging import get_logger, setup_logging
from app.metrics import BALANCE_UPSERTS_TOTAL, CONSUMER_PROCESSING_SECONDS
from app.services.balances import signed_amount
from app.tracing import current_trace_id, extract_context_from_kafka_headers, get_tracer, inject_trace_headers, setup_tracing
from app.utils.idempotency import mark_processed
from app.utils.time import now_utc_iso

logger = get_logger(__name__)
tracer = get_tracer(__name__)


async def run() -> None:
    setup_logging()
    setup_tracing("balance-projector-consumer")

    settings = get_settings()
    serde = get_serde()
    pool = await init_pg_pool()
    consumer = build_consumer(
        group_id=settings.balance_projector_group_id,
        topics=[settings.ledger_entry_batches_topic],
        client_suffix="balance-projector",
    )
    producer = KafkaProducer(client_id_suffix="balance-projector")
    dlq = DlqPublisher(stage="balance-projector")
    autoscaling = WorkerAutoscalingMetrics(worker_name="balance-projector")

    running = True
    processed_batches = 0

    def stop_handler(*_: object) -> None:
        nonlocal running
        running = False

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop_handler)

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

            try:
                parent_ctx = extract_context_from_kafka_headers(msg.headers())
                with tracer.start_as_current_span("consume.ledger_entry_batches.balance", context=parent_ctx):
                    timer = CONSUMER_PROCESSING_SECONDS.labels(
                        consumer="balance-projector",
                        topic=msg.topic(),
                    ).time()
                    with timer:
                        deserialized = serde.deserialize_ledger_entry_batch(msg.value())
                        schema_id = deserialized.schema_id
                        payload_dict = serde.ledger_batch_to_dict(deserialized.message)
                        correlation_id = payload_dict["correlation_id"]

                        async with pool.acquire() as conn:
                            async with conn.transaction():
                                with tracer.start_as_current_span("db.balance_projector.idempotency"):
                                    first_time = await mark_processed(
                                        conn,
                                        "balance-projector",
                                        payload_dict["batch_id"],
                                    )
                                if not first_time:
                                    consumer.commit(msg)
                                    continue

                                for entry in payload_dict["entries"]:
                                    delta = signed_amount(entry["side"], entry["amount"])
                                    with tracer.start_as_current_span("db.account_balance_upsert"):
                                        await conn.execute(
                                            """
                                            INSERT INTO account_balances (workspace_id, account_id, asset, balance, updated_at)
                                            VALUES ($1, $2, $3, $4, NOW())
                                            ON CONFLICT (workspace_id, account_id, asset)
                                            DO UPDATE
                                              SET balance = account_balances.balance + EXCLUDED.balance,
                                                  updated_at = NOW()
                                            """,
                                            entry["workspace_id"],
                                            entry["account_id"],
                                            entry["asset"],
                                            delta,
                                        )
                                    BALANCE_UPSERTS_TOTAL.labels(
                                        asset=entry["asset"],
                                        workspace_id=entry["workspace_id"],
                                    ).inc()

                        processed_batches += 1
                        if processed_batches % settings.balance_snapshot_every_batches == 0:
                            async with pool.acquire() as conn:
                                with tracer.start_as_current_span("db.balance_snapshot_insert"):
                                    insert_result = await conn.execute(
                                        """
                                        INSERT INTO balance_snapshots (workspace_id, account_id, asset, balance, source_batch_id)
                                        SELECT workspace_id, account_id, asset, balance, $1
                                        FROM account_balances
                                        WHERE workspace_id = $2
                                        """,
                                        payload_dict["batch_id"],
                                        payload_dict["workspace_id"],
                                    )
                            snapshot_rows = 0
                            parts = insert_result.split()
                            if len(parts) == 3 and parts[2].isdigit():
                                snapshot_rows = int(parts[2])
                            snapshot_payload = {
                                "workspace_id": payload_dict["workspace_id"],
                                "batch_id": payload_dict["batch_id"],
                                "captured_at": now_utc_iso(),
                                "rows": snapshot_rows,
                            }
                            headers = inject_trace_headers(
                                {
                                    "correlation_id": payload_dict["correlation_id"],
                                    "trace_id": current_trace_id(),
                                }
                            )
                            producer.produce_sync(
                                topic=settings.balance_snapshots_topic,
                                key=payload_dict["workspace_id"],
                                value=json.dumps(snapshot_payload, ensure_ascii=True).encode("utf-8"),
                                headers=headers,
                            )

                        autoscaling.observe_processed(
                            consumer=consumer,
                            topic=msg.topic(),
                            partition=msg.partition(),
                            offset=msg.offset(),
                        )
                        consumer.commit(msg)

            except Exception as exc:
                log_consumer_error("balance-projector", exc)
                dlq.publish(
                    topic=settings.dlq_ledger_batches_topic,
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
        producer.flush()
        consumer.close()
        await close_pg_pool()


if __name__ == "__main__":
    asyncio.run(run())
