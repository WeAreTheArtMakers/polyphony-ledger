# 05 - Canlı Demo Planı ve Satış Akışı

## Demo Öncesi Checklist

1. `docker compose up --build -d`
2. Frontend: `http://localhost:3000`
3. Backend health: `http://localhost:8000/health`
4. Grafana: `http://localhost:3001` (`admin/admin`)
5. Jaeger: `http://localhost:16686`

## 20 Dakikalık Satış Demo Akışı

## Dakika 0-3: İş problemi

- Çok kaynaklı ödeme event’lerinde audit ve analizin aynı anda neden zor olduğunu anlat.

## Dakika 3-8: Canlı akış

- `/transactions` sayfasında seed generator başlat.
- Manuel ingest yap.
- `/dashboard` ve `/ledger`’da canlı güncellemeyi göster.

## Dakika 8-12: Analitik

- `/analytics` sayfasında volume/top accounts/netflow grafikleri göster.
- ClickHouse katmanının operasyonel DB’den ayrıldığını vurgula.

## Dakika 12-15: Gözlemlenebilirlik

- Grafana dashboard’larında throughput/DLQ/error panellerini göster.
- Jaeger’da `correlation_id` ile tek işlem trace’ini bul.

## Dakika 15-18: Dayanıklılık

- Replay endpoint (`/replay`) ile projection yeniden inşa senaryosunu göster.

## Dakika 18-20: Ticari kapanış

- Pilot kapsamı, başarı metrikleri ve 30 günlük planı öner.

## Demo Sırasında Kritik Mesajlar

- "Kayıt doğruluğu immutable ledger ile güvence altında"
- "Gerçek zamanlı karar için OLAP katmanı ayrışık"
- "Arıza durumunda DLQ + replay ile kontrollü toparlanma"
