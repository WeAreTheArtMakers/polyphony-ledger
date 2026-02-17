# PolyPhonyLedger

<p align="center">
  <img src="assets/branding/polyphony-logo-128.png" alt="Polyphony Ledger Logo" width="96" />
</p>

Real-time crypto payments ledger demo with Redpanda, Schema Registry + Protobuf evolution, immutable Postgres double-entry ledger, replayable projections, ClickHouse OLAP, OpenTelemetry tracing, Prometheus/Grafana metrics, and a Next.js realtime UI.

## Architecture

```text
                              +------------------------------+
                              |          Frontend            |
                              |  Next.js + WS + Recharts     |
                              +---------------+--------------+
                                              |
                                              | REST + WS
                                              v
+-------------------------+      +------------+-------------+       +---------------------+
|  Seed Traffic Generator |----->| FastAPI Ingest API       |------>| tx_raw (Redpanda)   |
|  (/tx/generator/*)      |      | /tx/ingest + OTel spans  |       +----------+----------+
+-------------------------+      +--------------------------+                  |
                                                                                 v
                                                                       +---------+---------+
                                                                       | validator-cg      |
                                                                       | tx_raw -> tx_valid|
                                                                       +---------+---------+
                                                                                 |
                                                                                 v
                                                                       +---------+---------+
                                                                       | ledger-writer-cg  |
                                                                       | immutable ledger + |
                                                                       | outbox insert      |
                                                                       +---------+---------+
                                                                                 |
                                                                                 v
                                                                       +---------+---------+
                                                                       | outbox publisher   |
                                                                       | ledger_entry_batch |
                                                                       +---------+---------+
                                                                                 |
                               +----------------------+--------------------------+----------------------+
                               |                      |                                                 |
                               v                      v                                                 v
                     +---------+---------+   +--------+---------+                           +-----------+----------+
                     | balance-projector |   | clickhouse-writer|                           | DLQ topics per stage |
                     | account_balances  |   | CH raw + MVs      |                           | + PII redaction      |
                     +---------+---------+   +--------+---------+                           +----------------------+
                               |                      |
                               v                      v
                     +---------+---------+   +--------+---------+
                     | Postgres projection|  | ClickHouse OLAP  |
                     | replayable         |  | volume/netflow   |
                     +--------------------+  +------------------+

Telemetry path: backend + workers -> OTel Collector -> Jaeger
Metrics path: backend -> Prometheus -> Grafana
```

## Stack

- Streaming: Redpanda (Kafka API + built-in Schema Registry)
- Contracts: Protobuf + Schema Registry wire format (`magic-byte + schema-id + protobuf`)
- Tracing: OpenTelemetry SDK + Collector + Jaeger
- OLTP: Postgres (`events`, `ledger_*`, `processed_events`, `account_balances`, `outbox`)
- OLAP: ClickHouse raw table + materialized views
- Frontend: Next.js App Router + TypeScript + Tailwind + Recharts + WebSocket

## Sales/Business Docs (TR)

- Full Turkish sales + positioning + roadmap docs are under `/docs`.
- Start here: `docs/README.md`

## Run

```bash
cp .env.example .env
docker compose up --build
```

Exposed URLs:

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000)
- Prometheus: [http://localhost:9090](http://localhost:9090)
- Grafana: [http://localhost:3001](http://localhost:3001) (`admin/admin`)
- Jaeger: [http://localhost:16686](http://localhost:16686)
- Redpanda Console: [http://localhost:8080](http://localhost:8080)
- Schema Registry endpoint: [http://localhost:8081](http://localhost:8081)
- ClickHouse HTTP: [http://localhost:8123](http://localhost:8123)
- Sales Site: [http://localhost:3000/sales](http://localhost:3000/sales)

## Key API Endpoints

- `POST /tx/ingest`
- `GET /tx/recent/raw`
- `GET /tx/recent/validated`
- `POST /tx/generator/start?rate_per_sec=8`
- `POST /tx/generator/stop`
- `GET /ledger/recent`
- `GET /ledger/batches`
- `GET /balances?workspace_id=default`
- `POST /replay/from-ledger`
- `GET /analytics/volume-per-asset?minutes=60`
- `GET /analytics/netflow?account_id=acct_001&minutes=60`
- `GET /analytics/top-accounts?asset=USDT&minutes=60`
- `POST /telemetry/frontend`
- `GET /governance/me`
- `GET /governance/quota?workspace_id=default`
- `POST /governance/quota`
- `GET /governance/usage?workspace_id=default&months=6`
- `GET /metrics`
- `WS /ws/stream`

`POST /tx/ingest` contract note:

- `event_id` is mandatory and must be a valid UUID.
- `correlation_id` is optional (auto-generated if omitted).

## Sales Site + EN/TR Language Manager

- Route: `/sales`
- Default language: English
- Secondary language: Turkish
- Runtime language switch is handled by `frontend/public/language-manager.js`.

## Schema Evolution Demo (v1 -> v2)

`tx_raw` evolution is backward-compatible:

- v1 fields: `payer_account,payee_account,asset,amount,occurred_at,event_id,correlation_id`
- v2 adds optional: `payment_memo`, `workspace_id`, `client_id`

What this demo does:

1. On startup, backend registers `tx_raw` v1 and v2 under subject `tx_raw-value` with `BACKWARD` compatibility.
2. API can emit v1 wire format with `"force_v1": true`.
3. Consumers deserialize both using current v2 protobuf class; v1 messages remain readable.

Try it:

```bash
EVENT_ID_1="$(uuidgen | tr '[:upper:]' '[:lower:]')"
CORR_ID_1="$(uuidgen | tr '[:upper:]' '[:lower:]')"
curl -sS -X POST http://localhost:8000/tx/ingest \
  -H 'content-type: application/json' \
  -d '{
    "payer_account":"acct_001",
    "payee_account":"acct_002",
    "asset":"USDT",
    "amount":10,
    "event_id":"'"$EVENT_ID_1"'",
    "correlation_id":"'"$CORR_ID_1"'",
    "force_v1":true
  }'

EVENT_ID_2="$(uuidgen | tr '[:upper:]' '[:lower:]')"
CORR_ID_2="$(uuidgen | tr '[:upper:]' '[:lower:]')"
curl -sS -X POST http://localhost:8000/tx/ingest \
  -H 'content-type: application/json' \
  -d '{
    "payer_account":"acct_003",
    "payee_account":"acct_004",
    "asset":"USDT",
    "amount":15,
    "event_id":"'"$EVENT_ID_2"'",
    "correlation_id":"'"$CORR_ID_2"'",
    "payment_memo":"v2 memo",
    "workspace_id":"team-red",
    "client_id":"app-42"
  }'
```

## CI Quality Gates

Added mandatory CI gate workflow at `.github/workflows/ci-e2e.yml`.

It runs:

- Smoke checks (`/health`, ingest, ledger, analytics, replay): `python3 scripts/smoke_check.py`
- End-to-end pipeline checks (`tx_raw -> tx_validated -> outbox -> ledger_entry_batches -> balances -> clickhouse`): `python3 scripts/e2e_pipeline_check.py`

Run locally:

```bash
python3 scripts/smoke_check.py
python3 scripts/e2e_pipeline_check.py
```

## Frontend Quick Demo

To see the UI and streaming flow quickly:

1. Open [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
2. Open [http://localhost:3000/transactions](http://localhost:3000/transactions)
3. Click `Start Seed Generator` to produce continuous traffic
4. Submit a manual transaction from the ingest form
5. Watch:
   - dashboard live tables refresh via WebSocket
   - `/ledger` and `/analytics` update
   - `/traces` show distributed traces in Jaeger

Frontend telemetry is enabled by default in compose:

- `NEXT_PUBLIC_FE_TELEMETRY_ENABLED=true`
- `NEXT_PUBLIC_FE_TELEMETRY_SAMPLE_RATE=1`

Captured frontend telemetry:

- Web Vitals (CLS, LCP, INP, FCP, TTFB) via `useReportWebVitals`
- Browser runtime errors (`window.error`)
- Promise failures (`unhandledrejection`)

## Governance Controls (SSO-ready/RBAC/Quota/Metering)

New runtime controls are included:

- Header-based auth mode (gateway/SSO-ready): `AUTH_MODE=header`
- Workspace role guard: `viewer | operator | admin | owner`
- Ingest quota enforcement per workspace
- Usage metering endpoints under `/governance/*`

Environment defaults in `.env.example`:

- `AUTH_MODE=off`
- `DEFAULT_WORKSPACE_ROLE=owner`
- `DEFAULT_WORKSPACE_MONTHLY_TX_QUOTA=1000000`

## Exactly-Once Approximation

Pattern implemented:

- `processed_events(consumer_name,event_id)` for idempotent consumers
- Outbox table in same transaction as immutable ledger writes
- Separate outbox publisher with retries + exponential backoff
- Downstream consumers are idempotent, so duplicate publish is safe

This gives practical exactly-once behavior on top of at-least-once Kafka delivery.

## Ledger Rules

Double-entry convention (documented and implemented):

- `debit` increases balance
- `credit` decreases balance

Transfer payer -> payee amount X:

- payer: `credit X`
- payee: `debit X`

## Partitioning Strategy

Implemented keys:

- `tx_raw` / `tx_validated`: key = `payer_account`
- `ledger_entry_batches`: key = `tx_id`

Trade-offs:

- payer-based key preserves payer ordering and hotspot visibility per account
- tx_id key fans out independent transactions while keeping each batch ordered
- multi-tenant touch (`workspace_id` in v2): for stricter tenant isolation you can evolve key to `${workspace_id}:${payer_account}`; this increases locality by tenant but may reduce cross-tenant balancing depending on tenant skew

## Replay Process

`POST /replay/from-ledger`:

1. Truncates `account_balances`
2. Deterministically recomputes from immutable `ledger_entries`
3. Returns summary counts

UI has a dedicated `/replay` page to trigger this.

## ClickHouse OLAP Layer

Database: `polyphony`

- Raw table: `ledger_entries_raw` (`MergeTree`)
- Materialized Views:
  - `mv_volume_per_asset_1m`
  - `mv_netflow_per_account_1m`
  - `mv_top_accounts_5m`

Analytics endpoints query MV target tables for low-latency dashboards.

## Tracing

Implemented end-to-end tracing with OTel:

- API spans around `/tx/ingest`
- Producer and consumer spans around Kafka publish/consume
- DB spans for key write/read paths
- ClickHouse insert/query spans
- Trace context propagation via Kafka headers:
  - `traceparent`
  - `tracestate`
  - `correlation_id`

Find a transaction trace:

1. Call `/tx/ingest` and capture `correlation_id`
2. Open Jaeger UI
3. Search by tag `correlation_id=<value>`

## Grafana Alerts

Provisioned alert rules are loaded from:

- `infra/grafana/provisioning/alerting/polyphony_alerts.yml`

Preconfigured rules:

- `DLQ Messages Detected` (critical)
- `Frontend Client Errors Spike` (warning)
- `Poor Web Vitals Detected` (warning)

## DLQ and PII Redaction

Each stage has a dedicated DLQ topic:

- `dlq_tx_raw`
- `dlq_tx_validated`
- `dlq_ledger_batches`
- `dlq_clickhouse`

DLQ envelope includes:

- `trace_id`
- `correlation_id`
- `schema_id`
- redacted payload (account/client identifiers masked)

## Frontend Pages

- `/dashboard`: KPIs + live ledger/balance snapshots
- `/transactions`: ingest form + raw/validated tables + seed generator toggle
- `/ledger`: ledger entries + grouped batches
- `/analytics`: ClickHouse chart views
- `/replay`: projection rebuild controls
- `/traces`: Jaeger embed/link

Made with ❤️ WeAreTheArtMakers
