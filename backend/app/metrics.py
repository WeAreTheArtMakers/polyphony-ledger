from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "polyphony_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

TX_INGESTED_TOTAL = Counter(
    "polyphony_tx_ingested_total",
    "Total ingested raw transactions",
    ["version", "asset", "workspace_id"],
)

TX_VALIDATED_TOTAL = Counter(
    "polyphony_tx_validated_total",
    "Total validated transactions",
    ["asset", "workspace_id"],
)

LEDGER_ENTRIES_WRITTEN_TOTAL = Counter(
    "polyphony_ledger_entries_written_total",
    "Total ledger entries written",
    ["asset", "workspace_id"],
)

BALANCE_UPSERTS_TOTAL = Counter(
    "polyphony_balance_upserts_total",
    "Total account balance upserts",
    ["asset", "workspace_id"],
)

DLQ_MESSAGES_TOTAL = Counter(
    "polyphony_dlq_messages_total",
    "Total DLQ messages published",
    ["stage", "topic"],
)

OUTBOX_PUBLISHED_TOTAL = Counter(
    "polyphony_outbox_published_total",
    "Total outbox messages published",
    ["topic"],
)

CONSUMER_ERRORS_TOTAL = Counter(
    "polyphony_consumer_errors_total",
    "Total consumer processing errors",
    ["consumer"],
)

CONSUMER_PROCESSING_SECONDS = Histogram(
    "polyphony_consumer_processing_seconds",
    "Message processing duration in seconds",
    ["consumer", "topic"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

CLICKHOUSE_INSERT_SECONDS = Histogram(
    "polyphony_clickhouse_insert_seconds",
    "ClickHouse insert duration in seconds",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

INFLIGHT_WS_CONNECTIONS = Gauge(
    "polyphony_ws_connections",
    "Current websocket client connections",
)
