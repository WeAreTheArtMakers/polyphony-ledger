# Kabiliyetler ve Mimari

## Streaming Akisi

1. `tx_raw` ingest
2. validator dogrulama/normalize
3. immutable ledger yazimi + outbox
4. outbox ile `ledger_entry_batches` yayini
5. bakiye projection guncellemesi
6. ClickHouse analitik yazimi

## Veri Modeli Guclu Yonleri

- append-only event ve ledger kayitlari
- projection icin deterministik replay
- her tuketici asamasinda idempotency anahtarlari

## Gozlemlenebilirlik

- OpenTelemetry trace context propagation (`traceparent`, `tracestate`, `correlation_id`)
- throughput, retry, hata ve quota metrikleri
- Grafana dashboard ve alert kurallari
- Jaeger ile transaction bazli inceleme

## Frontend ve Gercek Zamanli Deneyim

- websocket ile canli ledger/balance guncellemeleri
- ClickHouse materialized view tabanli analitik ekranlari
- frontend telemetry (web vitals + client errors)
