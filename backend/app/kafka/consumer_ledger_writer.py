from __future__ import annotations

import asyncio
import json
import signal

from app.config import get_settings
from app.db.session import close_pg_pool, init_pg_pool
from app.kafka.dlq import DlqPublisher
from app.kafka.producer import build_consumer, log_consumer_error
from app.kafka.serde import get_serde
from app.kafka.worker_metrics import WorkerAutoscalingMetrics
from app.logging import get_logger, setup_logging
from app.metrics import CONSUMER_PROCESSING_SECONDS, LEDGER_ENTRIES_WRITTEN_TOTAL
from app.services.ledger import build_batch_payload, build_double_entries
from app.tracing import current_trace_id, extract_context_from_kafka_headers, get_tracer, inject_trace_headers, setup_tracing
from app.utils.idempotency import mark_processed

logger = get_logger(__name__)
tracer = get_tracer(__name__)


async def run() -> None:
    setup_logging()
    setup_tracing("ledger-writer-consumer")

    settings = get_settings()
    serde = get_serde()
    pool = await init_pg_pool()
    consumer = build_consumer(
        group_id=settings.ledger_writer_group_id,
        topics=[settings.tx_validated_topic],
        client_suffix="ledger-writer",
    )
    dlq = DlqPublisher(stage="ledger-writer")
    autoscaling = WorkerAutoscalingMetrics(worker_name="ledger-writer")

    running = True

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
                with tracer.start_as_current_span("consume.tx_validated", context=parent_ctx):
                    timer = CONSUMER_PROCESSING_SECONDS.labels(
                        consumer="ledger-writer",
                        topic=msg.topic(),
                    ).time()
                    with timer:
                        deserialized = serde.deserialize_tx_validated(msg.value())
                        schema_id = deserialized.schema_id
                        payload_dict = serde.tx_validated_to_dict(deserialized.message)
                        correlation_id = payload_dict["correlation_id"]

                        entries = build_double_entries(
                            tx_id=payload_dict["tx_id"],
                            workspace_id=payload_dict["workspace_id"],
                            payer_account=payload_dict["payer_account"],
                            payee_account=payload_dict["payee_account"],
                            asset=payload_dict["asset"],
                            amount=payload_dict["amount"],
                            correlation_id=payload_dict["correlation_id"],
                            occurred_at=payload_dict["occurred_at"],
                        )

                        batch_payload = build_batch_payload(
                            tx_id=payload_dict["tx_id"],
                            event_id=payload_dict["event_id"],
                            correlation_id=payload_dict["correlation_id"],
                            workspace_id=payload_dict["workspace_id"],
                            occurred_at=payload_dict["occurred_at"],
                            entries=entries,
                        )
                        outbox_payload = serde.serialize_ledger_entry_batch(batch_payload)

                        outbox_headers = inject_trace_headers(
                            {
                                "correlation_id": payload_dict["correlation_id"],
                                "trace_id": current_trace_id(),
                            }
                        )

                        async with pool.acquire() as conn:
                            async with conn.transaction():
                                with tracer.start_as_current_span("db.ledger_writer.idempotency"):
                                    first_time = await mark_processed(
                                        conn,
                                        "ledger-writer",
                                        payload_dict["event_id"],
                                    )
                                if not first_time:
                                    consumer.commit(msg)
                                    continue

                                with tracer.start_as_current_span("db.ledger_transaction_insert"):
                                    await conn.execute(
                                        """
                                        INSERT INTO ledger_transactions
                                          (tx_id, event_id, workspace_id, payer_account, payee_account, asset, amount, correlation_id, occurred_at)
                                        VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, $9)
                                        """,
                                        payload_dict["tx_id"],
                                        payload_dict["event_id"],
                                        payload_dict["workspace_id"],
                                        payload_dict["payer_account"],
                                        payload_dict["payee_account"],
                                        payload_dict["asset"],
                                        payload_dict["amount"],
                                        payload_dict["correlation_id"],
                                        payload_dict["occurred_at"],
                                    )

                                with tracer.start_as_current_span("db.ledger_entries_insert"):
                                    await conn.executemany(
                                        """
                                        INSERT INTO ledger_entries
                                          (tx_id, workspace_id, account_id, side, asset, amount, correlation_id, occurred_at)
                                        VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8)
                                        """,
                                        [
                                            (
                                                entry["tx_id"],
                                                entry["workspace_id"],
                                                entry["account_id"],
                                                entry["side"],
                                                entry["asset"],
                                                entry["amount"],
                                                entry["correlation_id"],
                                                entry["occurred_at"],
                                            )
                                            for entry in entries
                                        ],
                                    )

                                with tracer.start_as_current_span("db.outbox_insert"):
                                    await conn.execute(
                                        """
                                        INSERT INTO outbox (topic, key, workspace_id, payload, headers)
                                        VALUES ($1, $2, $3, $4, $5::jsonb)
                                        """,
                                        settings.ledger_entry_batches_topic,
                                        payload_dict["tx_id"],
                                        payload_dict["workspace_id"],
                                        outbox_payload,
                                        json.dumps(outbox_headers),
                                    )

                        for entry in entries:
                            LEDGER_ENTRIES_WRITTEN_TOTAL.labels(
                                asset=entry["asset"],
                                workspace_id=entry["workspace_id"],
                            ).inc()
                        autoscaling.observe_processed(
                            consumer=consumer,
                            topic=msg.topic(),
                            partition=msg.partition(),
                            offset=msg.offset(),
                        )
                        consumer.commit(msg)

            except Exception as exc:
                log_consumer_error("ledger-writer", exc)
                dlq.publish(
                    topic=settings.dlq_tx_validated_topic,
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


if __name__ == "__main__":
    asyncio.run(run())
