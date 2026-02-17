from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass
from typing import Any

from confluent_kafka import Consumer, KafkaError, Producer
from confluent_kafka.admin import AdminClient

from app.config import get_settings
from app.logging import get_logger
from app.metrics import (
    CONSUMER_ERRORS_TOTAL,
    KAFKA_STARTUP_READY_SECONDS,
    KAFKA_STARTUP_READY_STATE,
    KAFKA_STARTUP_RETRIES_TOTAL,
    PRODUCER_RETRIES_TOTAL,
)

logger = get_logger(__name__)


@dataclass
class DeliveryMeta:
    topic: str
    partition: int
    offset: int


def _classify_producer_error(error: Exception) -> str:
    message = str(error).lower()
    if "unknown topic" in message or "unknown_topic_or_part" in message:
        return "unknown_topic"
    if "leader" in message and "available" in message:
        return "leader_unavailable"
    if "timeout" in message or "timed out" in message:
        return "timeout"
    if "broker" in message or "transport" in message:
        return "broker_unavailable"
    return "other"


def _topic_ready(topic_meta: Any) -> bool:
    if topic_meta is None:
        return False
    topic_error = getattr(topic_meta, "error", None)
    if topic_error is not None and hasattr(topic_error, "code") and topic_error.code() != KafkaError.NO_ERROR:
        return False
    partitions = getattr(topic_meta, "partitions", {})
    if not partitions:
        return False
    for partition_meta in partitions.values():
        if getattr(partition_meta, "leader", -1) < 0:
            return False
    return True


def wait_for_topics(
    topics: list[str],
    component: str,
    timeout_seconds: float | None = None,
) -> None:
    settings = get_settings()
    wanted = sorted({topic.strip() for topic in topics if topic.strip()})
    if not wanted:
        return

    timeout = timeout_seconds or settings.kafka_startup_timeout_seconds
    admin = AdminClient(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "client.id": f"{settings.kafka_client_id}-{component}-readiness",
        }
    )

    KAFKA_STARTUP_READY_STATE.labels(component=component).set(0)
    started = time.monotonic()
    backoff_seconds = 0.25
    pending = wanted

    while True:
        try:
            metadata = admin.list_topics(timeout=5.0)
            pending = [topic for topic in wanted if not _topic_ready(metadata.topics.get(topic))]
            if not pending:
                elapsed = time.monotonic() - started
                KAFKA_STARTUP_READY_SECONDS.labels(component=component).observe(elapsed)
                KAFKA_STARTUP_READY_STATE.labels(component=component).set(1)
                logger.info(
                    "kafka_topics_ready",
                    extra={"component": component, "topics": wanted, "seconds": round(elapsed, 3)},
                )
                return
            reason = "topics_not_ready"
        except Exception as exc:
            reason = "metadata_error"
            logger.warning(
                "kafka_readiness_metadata_error",
                extra={"component": component, "error": str(exc)},
            )

        elapsed = time.monotonic() - started
        if elapsed >= timeout:
            KAFKA_STARTUP_READY_STATE.labels(component=component).set(0)
            raise TimeoutError(
                f"kafka topic readiness timeout for component={component}; pending_topics={pending}; timeout={timeout}s"
            )

        KAFKA_STARTUP_RETRIES_TOTAL.labels(component=component, reason=reason).inc()
        sleep_seconds = min(5.0, backoff_seconds) + random.uniform(0, min(5.0, backoff_seconds) * 0.2)
        logger.warning(
            "kafka_startup_retry",
            extra={
                "component": component,
                "reason": reason,
                "pending_topics": pending,
                "sleep_seconds": round(sleep_seconds, 3),
                "elapsed_seconds": round(elapsed, 3),
            },
        )
        time.sleep(sleep_seconds)
        backoff_seconds = min(5.0, backoff_seconds * 2)


class KafkaProducer:
    def __init__(self, client_id_suffix: str = "producer") -> None:
        settings = get_settings()
        self._client_id = f"{settings.kafka_client_id}-{client_id_suffix}"
        self._max_retries = max(1, int(settings.producer_max_retries))
        self._retry_base_seconds = max(0.01, float(settings.producer_retry_base_ms) / 1000.0)
        self._producer = Producer(
            {
                "bootstrap.servers": settings.kafka_bootstrap_servers,
                "client.id": self._client_id,
                "enable.idempotence": True,
                "acks": "all",
                "linger.ms": 10,
            }
        )

    def _produce_once(
        self,
        topic: str,
        key: str,
        value: bytes,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> DeliveryMeta:
        done = threading.Event()
        state: dict[str, Any] = {}
        kafka_headers = [(k, v.encode("utf-8")) for k, v in (headers or {}).items()]

        def callback(err: KafkaError | None, msg: Any) -> None:
            if err is not None:
                state["error"] = err
            else:
                state["meta"] = DeliveryMeta(
                    topic=msg.topic(),
                    partition=msg.partition(),
                    offset=msg.offset(),
                )
            done.set()

        self._producer.produce(topic=topic, key=key, value=value, headers=kafka_headers, on_delivery=callback)
        deadline = time.monotonic() + timeout
        while not done.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._producer.flush(0)
                break
            self._producer.poll(min(0.2, remaining))
        if not done.is_set():
            raise TimeoutError(f"delivery timeout for topic={topic}")
        if "error" in state:
            raise RuntimeError(str(state["error"]))
        return state["meta"]

    def produce_sync(
        self,
        topic: str,
        key: str,
        value: bytes,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> DeliveryMeta:
        for attempt in range(1, self._max_retries + 1):
            try:
                return self._produce_once(
                    topic=topic,
                    key=key,
                    value=value,
                    headers=headers,
                    timeout=timeout,
                )
            except Exception as exc:
                if attempt >= self._max_retries:
                    raise
                reason = _classify_producer_error(exc)
                PRODUCER_RETRIES_TOTAL.labels(
                    producer=self._client_id,
                    topic=topic,
                    reason=reason,
                ).inc()
                backoff_seconds = min(5.0, self._retry_base_seconds * (2 ** (attempt - 1)))
                sleep_seconds = backoff_seconds + random.uniform(0, backoff_seconds * 0.2)
                logger.warning(
                    "producer_retry_backoff",
                    extra={
                        "producer": self._client_id,
                        "topic": topic,
                        "attempt": attempt,
                        "max_retries": self._max_retries,
                        "reason": reason,
                        "sleep_seconds": round(sleep_seconds, 3),
                        "error": str(exc),
                    },
                )
                time.sleep(sleep_seconds)
        raise RuntimeError(f"unreachable producer retry path for topic={topic}")

    def flush(self, timeout: float = 10.0) -> None:
        self._producer.flush(timeout)


def build_consumer(group_id: str, topics: list[str], client_suffix: str) -> Consumer:
    settings = get_settings()
    component = f"consumer:{client_suffix}"
    wait_for_topics(
        topics=topics,
        component=component,
        timeout_seconds=settings.kafka_startup_timeout_seconds,
    )
    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "allow.auto.create.topics": False,
            "client.id": f"{settings.kafka_client_id}-{client_suffix}",
        }
    )
    consumer.subscribe(topics)
    return consumer


def log_consumer_error(consumer_name: str, error: Exception) -> None:
    logger.error("consumer_error", extra={"consumer": consumer_name, "error": str(error)})
    CONSUMER_ERRORS_TOTAL.labels(consumer=consumer_name).inc()
