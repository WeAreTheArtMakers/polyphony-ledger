from __future__ import annotations

import time
from collections import defaultdict, deque

from confluent_kafka import Consumer, TopicPartition

from app.config import get_settings
from app.logging import get_logger
from app.metrics import WORKER_AUTOSCALE_TARGET, WORKER_CONSUMER_LAG, WORKER_MESSAGES_PROCESSED_TOTAL, WORKER_THROUGHPUT_PER_MINUTE

logger = get_logger(__name__)


class WorkerAutoscalingMetrics:
    """Tracks lag + throughput signals that autoscalers can consume from Prometheus."""

    def __init__(self, worker_name: str, window_seconds: float = 60.0) -> None:
        self.worker_name = worker_name
        self.window_seconds = max(10.0, window_seconds)
        self._processed_windows: dict[str, deque[float]] = defaultdict(deque)
        settings = get_settings()
        WORKER_AUTOSCALE_TARGET.labels(worker=self.worker_name, metric="lag").set(float(settings.autoscale_target_lag))
        WORKER_AUTOSCALE_TARGET.labels(worker=self.worker_name, metric="throughput_per_minute").set(
            float(settings.autoscale_target_throughput_per_minute)
        )

    def observe_processed(self, consumer: Consumer, topic: str, partition: int, offset: int) -> None:
        self._observe_throughput(topic=topic)
        self._observe_lag(consumer=consumer, topic=topic, partition=partition, offset=offset)

    def _observe_throughput(self, topic: str) -> None:
        now = time.monotonic()
        window = self._processed_windows[topic]
        window.append(now)
        cutoff = now - self.window_seconds
        while window and window[0] < cutoff:
            window.popleft()

        throughput_per_min = (len(window) / self.window_seconds) * 60.0
        WORKER_MESSAGES_PROCESSED_TOTAL.labels(worker=self.worker_name, topic=topic).inc()
        WORKER_THROUGHPUT_PER_MINUTE.labels(worker=self.worker_name, topic=topic).set(throughput_per_min)

    def _observe_lag(self, consumer: Consumer, topic: str, partition: int, offset: int) -> None:
        try:
            low, high = consumer.get_watermark_offsets(TopicPartition(topic, partition), timeout=1.0, cached=False)
            _ = low
            lag = max(0, int(high) - int(offset) - 1)
            WORKER_CONSUMER_LAG.labels(
                worker=self.worker_name,
                topic=topic,
                partition=str(partition),
            ).set(lag)
        except Exception as exc:
            logger.debug(
                "worker_lag_sampling_failed",
                extra={"worker": self.worker_name, "topic": topic, "partition": partition, "error": str(exc)},
            )
