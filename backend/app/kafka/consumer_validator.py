from __future__ import annotations

import asyncio
import json
import signal

from app.config import get_settings
from app.db.session import close_pg_pool, init_pg_pool
from app.kafka.dlq import DlqPublisher
from app.kafka.producer import KafkaProducer, build_consumer, log_consumer_error
from app.kafka.serde import get_serde
from app.logging import get_logger, setup_logging
from app.metrics import CONSUMER_PROCESSING_SECONDS, TX_VALIDATED_TOTAL
from app.services.validate_tx import ValidationError, normalize_and_validate
from app.tracing import (
    current_trace_id,
    extract_context_from_kafka_headers,
    get_tracer,
    inject_trace_headers,
    setup_tracing,
)
from app.utils.idempotency import mark_processed

logger = get_logger(__name__)
tracer = get_tracer(__name__)


async def run() -> None:
    setup_logging()
    setup_tracing("validator-consumer")

    settings = get_settings()
    serde = get_serde()
    pool = await init_pg_pool()
    consumer = build_consumer(
        group_id=settings.validator_group_id,
        topics=[settings.tx_raw_topic],
        client_suffix="validator",
    )
    producer = KafkaProducer(client_id_suffix="validator")
    dlq = DlqPublisher(stage="validator")

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
                with tracer.start_as_current_span("consume.tx_raw", context=parent_ctx) as span:
                    timer = CONSUMER_PROCESSING_SECONDS.labels(
                        consumer="validator",
                        topic=msg.topic(),
                    ).time()
                    with timer:
                        deserialized = serde.deserialize_tx_raw(msg.value())
                        schema_id = deserialized.schema_id
                        payload_dict = serde.tx_raw_to_dict(deserialized.message)
                        correlation_id = payload_dict["correlation_id"]

                        span.set_attribute("event_id", payload_dict["event_id"])
                        span.set_attribute("correlation_id", correlation_id)
                        span.set_attribute("payer", payload_dict["payer_account"])
                        span.set_attribute("asset", payload_dict["asset"])

                        normalized = normalize_and_validate(
                            payload_dict,
                            allowed_assets=settings.allowed_assets_set,
                        )

                        async with pool.acquire() as conn:
                            async with conn.transaction():
                                with tracer.start_as_current_span("db.validator.idempotency"):
                                    first_time = await mark_processed(conn, "validator", normalized.event_id)
                                if not first_time:
                                    consumer.commit(msg)
                                    continue

                                with tracer.start_as_current_span("db.events_insert"):
                                    await conn.execute(
                                        """
                                        INSERT INTO events (event_id, event_type, workspace_id, correlation_id, payload)
                                        VALUES ($1::uuid, $2, $3, $4, $5::jsonb)
                                        ON CONFLICT (event_id) DO NOTHING
                                        """,
                                        normalized.event_id,
                                        "tx_raw_validated",
                                        normalized.workspace_id,
                                        normalized.correlation_id,
                                        json.dumps(payload_dict, default=str),
                                    )

                        out_payload = serde.serialize_tx_validated(normalized.to_dict())
                        headers = inject_trace_headers({
                            "correlation_id": normalized.correlation_id,
                            "trace_id": current_trace_id(),
                        })
                        producer.produce_sync(
                            topic=settings.tx_validated_topic,
                            key=normalized.payer_account,
                            value=out_payload,
                            headers=headers,
                        )
                        TX_VALIDATED_TOTAL.labels(
                            asset=normalized.asset,
                            workspace_id=normalized.workspace_id,
                        ).inc()
                        consumer.commit(msg)

            except (ValidationError, ValueError) as exc:
                log_consumer_error("validator", exc)
                dlq.publish(
                    topic=settings.dlq_tx_raw_topic,
                    source_topic=msg.topic(),
                    key=key,
                    error=exc,
                    correlation_id=correlation_id,
                    schema_id=schema_id,
                    decoded_payload=payload_dict,
                    raw_payload=msg.value(),
                )
                consumer.commit(msg)
            except Exception as exc:
                log_consumer_error("validator", exc)
                dlq.publish(
                    topic=settings.dlq_tx_raw_topic,
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
