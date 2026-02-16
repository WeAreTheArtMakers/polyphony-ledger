from __future__ import annotations

import base64
import json
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.kafka.producer import KafkaProducer
from app.logging import get_logger
from app.metrics import DLQ_MESSAGES_TOTAL
from app.tracing import current_trace_id
from app.utils.time import now_utc_iso

logger = get_logger(__name__)


def _mask(value: str) -> str:
    if len(value) <= 4:
        return "****"
    return f"{value[:2]}***{value[-2:]}"


def redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(payload)
    for key in ["payer_account", "payee_account", "account_id", "client_id"]:
        if key in redacted and redacted[key]:
            redacted[key] = _mask(str(redacted[key]))
    return redacted


def _json_default(value: Any) -> str:
    if isinstance(value, (Decimal, datetime, UUID)):
        return str(value)
    if isinstance(value, (bytes, bytearray)):
        return base64.b64encode(bytes(value)).decode("ascii")
    return str(value)


class DlqPublisher:
    def __init__(self, stage: str) -> None:
        self.stage = stage
        self.producer = KafkaProducer(client_id_suffix=f"{stage}-dlq")

    def publish(
        self,
        topic: str,
        source_topic: str,
        key: str,
        error: Exception,
        correlation_id: str,
        schema_id: int | None,
        decoded_payload: dict[str, Any] | None,
        raw_payload: bytes | None,
    ) -> None:
        envelope = {
            "stage": self.stage,
            "source_topic": source_topic,
            "error": str(error),
            "trace_id": current_trace_id(),
            "correlation_id": correlation_id,
            "schema_id": schema_id,
            "payload": redact_payload(decoded_payload or {}),
            "raw_payload_b64": base64.b64encode(raw_payload or b"").decode("ascii"),
            "ts": now_utc_iso(),
        }
        body = json.dumps(envelope, ensure_ascii=True, default=_json_default).encode("utf-8")
        self.producer.produce_sync(topic=topic, key=key, value=body)
        DLQ_MESSAGES_TOTAL.labels(stage=self.stage, topic=topic).inc()
        logger.error("dlq_published", extra={"stage": self.stage, "topic": topic, "correlation_id": correlation_id})
