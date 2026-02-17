# 02 - Ürün Vizyonu ve Çözdüğü Problemler

## Vizyon

Global ölçekte çalışan kripto ödeme ekiplerine, denetlenebilir muhasebe doğruluğu ile gerçek zamanlı finansal analitiği tek platformda sunmak.

## Hedeflenen Problem Alanları

## 1) Veri Tutarlılığı

- Sorun: Yüksek throughput altında duplicated event, out-of-order event, retry kaynaklı tekrar yazımlar
- Çözüm: `processed_events` tablosu ile tüketici bazlı idempotency + outbox yayın modeli

## 2) Ledger Doğruluğu

- Sorun: Tek satırlık bakiye güncellemeleri geriye dönük ispat üretmekte yetersiz kalır
- Çözüm: immutable `ledger_transactions` + `ledger_entries` çift kayıt modeli

## 3) Gözlemlenebilirlik Açığı

- Sorun: Bir işlemin API’den başlayıp hangi aşamada geciktiği görülemez
- Çözüm: OpenTelemetry trace context propagation (`traceparent`, `tracestate`, `correlation_id`)

## 4) Analitik Gecikme

- Sorun: Operasyonel DB’de karmaşık sorgular ürün performansını bozar
- Çözüm: ClickHouse’a stream insert + materialized view’lar

## 5) Şema Evrimi Riski

- Sorun: Event modeli değiştiğinde eski tüketiciler kırılır
- Çözüm: Schema Registry + Protobuf backward-compatible evrim (v1 -> v2)

## Platform Değeri

- "Kayıt doğruluğu" ve "analitik hız" arasında taviz vermez.
- Replay kabiliyeti ile projection bozulmalarını kontrollü telafi eder.
- DLQ ile hata izolasyonu sağlar ve işlem kaybını önler.

## Ürünleşme Potansiyeli

- API-first: partner onboarding hızlı
- Tenant-aware evrim (`workspace_id`): çoklu müşteri izolasyonuna hazır
- Gözlemlenebilirlik-first: enterprise satış görüşmesinde güven artırır
