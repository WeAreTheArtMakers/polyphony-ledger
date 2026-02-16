from __future__ import annotations

from typing import Any

from opentelemetry import propagate, trace
from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import get_settings

_INITIALIZED = False


class DictSetter:
    def set(self, carrier: dict[str, str], key: str, value: str) -> None:
        carrier[key] = value


class KafkaHeaderGetter:
    def get(self, carrier: dict[str, str], key: str) -> list[str] | None:
        value = carrier.get(key)
        if value is None:
            return None
        return [value]

    def keys(self, carrier: dict[str, str]) -> list[str]:
        return list(carrier.keys())


def setup_tracing(service_name: str) -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return

    settings = get_settings()
    if not settings.otel_enabled:
        _INITIALIZED = True
        return

    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _INITIALIZED = True


def instrument_fastapi(app: Any) -> None:
    FastAPIInstrumentor.instrument_app(app)


def get_tracer(name: str):
    return trace.get_tracer(name)


def inject_trace_headers(headers: dict[str, str]) -> dict[str, str]:
    propagate.inject(headers, setter=DictSetter())
    return headers


def extract_context_from_kafka_headers(headers: list[tuple[str, bytes]] | None) -> Context:
    if not headers:
        return Context()
    normalized: dict[str, str] = {}
    for key, value in headers:
        if value is None:
            continue
        normalized[key] = value.decode("utf-8", errors="ignore")
    return propagate.extract(normalized, getter=KafkaHeaderGetter())


def current_trace_id() -> str:
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if not ctx or not ctx.trace_id:
        return ""
    return format(ctx.trace_id, "032x")
