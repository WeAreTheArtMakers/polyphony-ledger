# Platform Overview

Polyphony Ledger is a real-time crypto payments platform that combines:

- immutable double-entry ledger correctness
- replayable operational projections
- streaming-native event processing
- low-latency OLAP analytics
- end-to-end observability

## Core Value

The platform is designed to remove the usual trade-off between accounting correctness and analytics speed.

## What It Delivers

- transaction-level traceability across API, Kafka, Postgres, and ClickHouse
- deterministic balance rebuild from immutable ledger entries
- governed schema evolution for event contracts
- isolated failure handling through stage-specific DLQ topics

## Primary Components

- Ingest/API: FastAPI
- Stream backbone: Redpanda (Kafka API)
- Event contracts: Schema Registry + Protobuf
- OLTP: Postgres
- OLAP: ClickHouse
- Observability: Prometheus, Grafana, OpenTelemetry, Jaeger
- UI: Next.js realtime dashboard and analytics views
