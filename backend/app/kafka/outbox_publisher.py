from __future__ import annotations

import asyncio
import json
import math
import signal

from app.config import get_settings
from app.db.session import close_pg_pool, init_pg_pool
from app.kafka.producer import KafkaProducer
from app.logging import get_logger, setup_logging
from app.metrics import OUTBOX_PUBLISHED_TOTAL
from app.tracing import get_tracer, setup_tracing

logger = get_logger(__name__)
tracer = get_tracer(__name__)


def _backoff_seconds(attempts: int) -> int:
    return min(60, int(math.pow(2, attempts)))


async def run() -> None:
    setup_logging()
    setup_tracing("outbox-publisher")

    settings = get_settings()
    pool = await init_pg_pool()
    producer = KafkaProducer(client_id_suffix="outbox")
    running = True

    def stop_handler(*_: object) -> None:
        nonlocal running
        running = False

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop_handler)

    try:
        while running:
            async with pool.acquire() as conn:
                with tracer.start_as_current_span("db.outbox_poll"):
                    async with conn.transaction():
                        rows = await conn.fetch(
                            """
                            SELECT id, topic, key, payload, headers, attempts
                            FROM outbox
                            WHERE published_at IS NULL
                              AND next_attempt_at <= NOW()
                            ORDER BY id ASC
                            LIMIT $1
                            FOR UPDATE SKIP LOCKED
                            """,
                            settings.outbox_batch_size,
                        )

                for row in rows:
                    with tracer.start_as_current_span("outbox.publish") as span:
                        span.set_attribute("outbox.id", row["id"])
                        span.set_attribute("kafka.topic", row["topic"])
                        try:
                            headers = row["headers"] or {}
                            if isinstance(headers, str):
                                headers = json.loads(headers)
                            producer.produce_sync(
                                topic=row["topic"],
                                key=row["key"],
                                value=bytes(row["payload"]),
                                headers=headers,
                            )
                            with tracer.start_as_current_span("db.outbox_mark_published"):
                                await conn.execute(
                                    "UPDATE outbox SET published_at = NOW(), last_error = NULL WHERE id = $1",
                                    row["id"],
                                )
                            OUTBOX_PUBLISHED_TOTAL.labels(topic=row["topic"]).inc()
                        except Exception as exc:
                            attempts = int(row["attempts"]) + 1
                            delay = _backoff_seconds(attempts)
                            with tracer.start_as_current_span("db.outbox_mark_retry"):
                                await conn.execute(
                                    """
                                    UPDATE outbox
                                    SET attempts = attempts + 1,
                                        last_error = $2,
                                        next_attempt_at = NOW() + make_interval(secs => $3)
                                    WHERE id = $1
                                    """,
                                    row["id"],
                                    str(exc),
                                    delay,
                                )
                            logger.error(
                                "outbox_publish_failed",
                                extra={"id": row["id"], "attempts": attempts, "error": str(exc)},
                            )

            await asyncio.sleep(settings.outbox_poll_interval_ms / 1000)
    finally:
        producer.flush()
        await close_pg_pool()


if __name__ == "__main__":
    asyncio.run(run())
