# 03 - Teknik Mimari ve Farklılaştırıcılar

## Mimari Özeti

- Ingest: FastAPI
- Stream Backbone: Redpanda (Kafka API)
- Contract Governance: Schema Registry + Protobuf
- OLTP: Postgres (immutable ledger + projection)
- OLAP: ClickHouse (real-time analytics)
- Observability: Prometheus + Grafana + OTel Collector + Jaeger
- Frontend: Next.js + WebSocket + Recharts

## Pipeline Aşamaları

1. `tx_raw` (API ingest)
2. `validator-cg` (doğrulama + normalize + events insert + tx_validated publish)
3. `ledger-writer-cg` (ledger tx + 2 entry + outbox atomik yazım)
4. `outbox-publisher` (ledger_entry_batches publish)
5. `balance-projector-cg` (account_balances projection)
6. `clickhouse-writer-cg` (OLAP yazımı)

## Neden Güçlü?

- Exactly-once approximation: outbox + idempotency
- Immutable audit trail: append-only ledger
- Replayability: projection yeniden inşa edilebilir
- Traceability: distributed tracing + correlation_id

## Teknik Farklılaştırıcılar

- Şema evrimi canlı gösterilebilir (v1/v2 birlikte tüketim)
- DLQ’lar stage bazında ayrılmış (hata sınırlandırma)
- Tenant alanı (`workspace_id`) ürünleşme için altyapıda hazır
- Frontend telemetry -> backend metrics -> alert zinciri tamam

## Tasarım Kararı: Partitioning

- `tx_raw/tx_validated` key=`payer_account`
  - avantaj: hesap bazlı sıralama ve yerellik
- `ledger_entry_batches` key=`tx_id`
  - avantaj: işlem bazlı batch bütünlüğü

## Enterprise Readiness Göstergeleri

- Structured JSON log
- Health + readiness endpoint
- CI e2e gate (pipeline uçtan uca doğrulama)
- Retry/backoff ve startup readiness metrikleri
