from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

from confluent_kafka import Consumer, KafkaError, Producer

from app.config import get_settings
from app.logging import get_logger
from app.metrics import CONSUMER_ERRORS_TOTAL

logger = get_logger(__name__)


@dataclass
class DeliveryMeta:
    topic: str
    partition: int
    offset: int


class KafkaProducer:
    def __init__(self, client_id_suffix: str = "producer") -> None:
        settings = get_settings()
        self._producer = Producer(
            {
                "bootstrap.servers": settings.kafka_bootstrap_servers,
                "client.id": f"{settings.kafka_client_id}-{client_id_suffix}",
                "enable.idempotence": True,
                "acks": "all",
                "linger.ms": 10,
            }
        )

    def produce_sync(
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

    def flush(self, timeout: float = 10.0) -> None:
        self._producer.flush(timeout)


def build_consumer(group_id: str, topics: list[str], client_suffix: str) -> Consumer:
    settings = get_settings()
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
