from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from app.logging import get_logger
from app.metrics import (
    FRONTEND_CLIENT_ERRORS_TOTAL,
    FRONTEND_WEB_VITAL_VALUE,
    FRONTEND_WEB_VITALS_TOTAL,
)
from app.tracing import get_tracer

router = APIRouter(prefix="/telemetry", tags=["observability"])
logger = get_logger(__name__)
tracer = get_tracer(__name__)

_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_LONG_NUMBER_RE = re.compile(r"\b\d{12,19}\b")
_BEARER_RE = re.compile(r"(?i)bearer\s+[a-z0-9\-\._~\+\/]+=*")


def _redact_text(raw: str | None, *, max_len: int) -> str | None:
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    value = _EMAIL_RE.sub("[redacted-email]", value)
    value = _LONG_NUMBER_RE.sub("[redacted-number]", value)
    value = _BEARER_RE.sub("Bearer [redacted-token]", value)
    if len(value) > max_len:
        return f"{value[:max_len]}...[truncated]"
    return value


def _route_bucket(path: str | None) -> str:
    if path is None:
        return "root"
    value = path.strip().split("?", 1)[0]
    if value in {"", "/"}:
        return "root"
    head = value.lstrip("/").split("/", 1)[0].strip().lower()
    return head[:48] if head else "root"


def _normalize_rating(rating: str | None) -> str:
    if rating in {"good", "needs-improvement", "poor"}:
        return rating
    return "unknown"


class FrontendTelemetryEvent(BaseModel):
    model_config = {"populate_by_name": True, "extra": "ignore"}

    event_type: Literal["web_vital", "client_error"] = Field(alias="type")
    name: str | None = Field(default=None, min_length=2, max_length=64)
    value: float | None = None
    rating: str | None = Field(default=None, max_length=32)
    metric_id: str | None = Field(default=None, alias="id", max_length=128)
    delta: float | None = None
    kind: str | None = Field(default=None, max_length=64)
    message: str | None = Field(default=None, max_length=4096)
    stack: str | None = Field(default=None, max_length=8192)
    path: str | None = Field(default="/", max_length=256)
    href: str | None = Field(default=None, max_length=512)
    session_id: str | None = Field(default=None, max_length=64)
    user_agent: str | None = Field(default=None, max_length=256)
    ts: datetime | None = None
    workspace_id: str | None = Field(default="default", max_length=64)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().upper()

    @field_validator("workspace_id")
    @classmethod
    def normalize_workspace_id(cls, value: str | None) -> str:
        if value is None:
            return "default"
        normalized = value.strip()
        return normalized if normalized else "default"


@router.post("/frontend")
async def ingest_frontend_telemetry(event: FrontendTelemetryEvent) -> dict[str, str]:
    route = _route_bucket(event.path)
    workspace_id = event.workspace_id or "default"
    timestamp = event.ts.astimezone(timezone.utc).isoformat() if event.ts else datetime.now(timezone.utc).isoformat()

    with tracer.start_as_current_span("api.telemetry.frontend") as span:
        span.set_attribute("telemetry.type", event.event_type)
        span.set_attribute("telemetry.route", route)
        span.set_attribute("workspace_id", workspace_id)

        if event.event_type == "web_vital":
            metric = event.name or "UNKNOWN"
            rating = _normalize_rating(event.rating)
            observed_value = max(0.0, float(event.value or 0.0))

            FRONTEND_WEB_VITALS_TOTAL.labels(
                metric=metric,
                rating=rating,
                route=route,
                workspace_id=workspace_id,
            ).inc()
            FRONTEND_WEB_VITAL_VALUE.labels(
                metric=metric,
                route=route,
                workspace_id=workspace_id,
            ).observe(observed_value)

            logger.info(
                "frontend_web_vital",
                extra={
                    "metric": metric,
                    "rating": rating,
                    "value": observed_value,
                    "delta": event.delta,
                    "route": route,
                    "workspace_id": workspace_id,
                    "metric_id": event.metric_id,
                    "session_id": event.session_id,
                    "ts_client": timestamp,
                },
            )
        else:
            kind = (event.kind or "error").strip().lower()[:64] or "error"
            message = _redact_text(event.message, max_len=800)
            stack = _redact_text(event.stack, max_len=1200)

            FRONTEND_CLIENT_ERRORS_TOTAL.labels(
                kind=kind,
                route=route,
                workspace_id=workspace_id,
            ).inc()

            logger.warning(
                "frontend_client_error",
                extra={
                    "kind": kind,
                    "error_message": message,
                    "stack_trace": stack,
                    "route": route,
                    "workspace_id": workspace_id,
                    "href": event.href,
                    "session_id": event.session_id,
                    "user_agent": event.user_agent,
                    "ts_client": timestamp,
                },
            )

    return {"status": "accepted"}
