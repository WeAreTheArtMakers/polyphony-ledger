# Capabilities and Architecture

## Streaming Pipeline

1. `tx_raw` ingest
2. validator normalization
3. immutable ledger write + outbox insert
4. outbox publish to `ledger_entry_batches`
5. balance projection update
6. ClickHouse analytics write

## Data Model Strengths

- append-only events and ledger entries
- deterministic replay for projections
- strict idempotency keys per consumer stage

## Observability

- OpenTelemetry traces with propagated context (`traceparent`, `tracestate`, `correlation_id`)
- Prometheus metrics for throughput, retries, errors, and quotas
- Grafana dashboards and alert rules
- Jaeger trace exploration for transaction-level debugging

## Frontend and Realtime UX

- websocket snapshots for live ledger/balance updates
- analytics dashboards over ClickHouse materialized views
- frontend telemetry capture (web vitals + client errors)
