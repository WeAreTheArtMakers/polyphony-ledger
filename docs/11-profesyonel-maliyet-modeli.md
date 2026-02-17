# 11 - Profesyonel Maliyet Modeli (Tam Stack)

Bu dokuman, `polyphony-ledger` tam stack'inin (Redpanda + Postgres + ClickHouse + Grafana + Jaeger + backend + frontend + workers) canli ortam maliyetini planlamak icin pratik bir model sunar.

## 1) Neden Free Tier Tam Uyumlu Degil?

Bu platformda birden fazla stateful servis ve surekli calisan worker zinciri var:

- broker (Redpanda)
- OLTP DB (Postgres)
- OLAP DB (ClickHouse)
- observability (Prometheus/Grafana/Jaeger)
- API + birden fazla worker

Free planlar genelde su kisitlara takilir:

- servis uyutma/sleep
- saatlik kota
- tek process/az RAM
- egress/build limitleri

## 2) Referans Fiyat Noktalari (17 Subat 2026 kontrolu)

Not: Fiyatlar saglayici tarafinda degisebilir; teklifte her zaman "guncel fiyat kontrol tarihi" yazin.

### Saglayici bazli referanslar

1. AWS Lightsail pricing sayfasinda:
   - 16 GB / 4 vCPU: 80 USD/ay
   - 32 GB / 8 vCPU: 160 USD/ay
2. DigitalOcean pricing sayfasinda (general purpose):
   - 16 GB / 4 vCPU: 126 USD/ay
   - 32 GB / 8 vCPU: 252 USD/ay
3. Northflank pricing sayfasinda Sandbox katmani:
   - 2 free service + 1 free database (demo icin limitli)
4. Render free dokumaninda:
   - 15 dk inaktivite sonrasi spin-down + aylik saat limitleri
5. Fly.io pricing dokumaninda:
   - yeni musteriler icin eski "free allowances" planlari devam etmiyor (legacy hesaplara ozel)
6. Oracle OCI Always Free dokumaninda:
   - A1 esdegeri 4 OCPU + 24 GB memory (idle reclaim ve kapasite siniri notu ile)
7. Hetzner cloud sayfasi:
   - tek node canli demo icin fiyat/performans odakli EU seceneklerinde sik tercih edilen alternatif

## 3) 3 Farkli Canliya Alma Seviyesi

## Seviye A - CV / Demo (Tek Node)

Amac:

- CV'de gostermek
- canli urun demosu yapmak
- kontrollu trafik

Onerilen kaynak:

- 8 vCPU / 16 GB RAM / 200+ GB NVMe

Aylik tahmini toplam:

- 80-220 USD (saglayiciya gore)

Icerik:

- tum servisler tek host'ta docker compose
- gunluk backup + temel monitoring

## Seviye B - Pilot (Ayrisik DB)

Amac:

- gercek trafik alt kumesi
- karsilastirmali KPI olcumu

Onerilen kaynak:

- app/workers node: 8 vCPU / 16 GB
- DB node: 8 vCPU / 32 GB

Aylik tahmini toplam:

- 250-700 USD

Icerik:

- Postgres ve ClickHouse ayri node
- daha guclu backup + runbook

## Seviye C - Enterprise Baslangic

Amac:

- SLA ve guvenlik odakli production

Onerilen kaynak:

- en az 3 node (app, broker, db)
- merkezi log + alert routing + yedeklilik

Aylik tahmini toplam:

- 800-2,500+ USD (trafik, retention ve SLA seviyesine gore)

## 4) Gizli Maliyet Kalemleri (Teklifte unutma)

- domain + TLS + WAF
- yedekleme depolama
- egress trafik
- log/metric retention
- on-call / operasyon is gucu

## 5) Satista Fiyatlandirma Stratejisi

Musteriye altyapi fiyati degil is etkisi sat:

- mutabakat suresinde azalma
- incident MTTR dususu
- audit hazirlik is gucu azalmasi

Model:

- Kurulum ucreti + aylik platform
- opsiyonel managed support
- hacim bazli usage katmani

## 6) Onerilen Baslangic

CV ve demo icin:

1. Tek node canli demo (Seviye A)
2. 30 gun KPI toplama
3. Sonra Pilot (Seviye B) teklifine gecis

## Kaynaklar

- https://aws.amazon.com/lightsail/pricing/
- https://www.digitalocean.com/pricing/droplets
- https://northflank.com/pricing
- https://render.com/free
- https://fly.io/docs/about/pricing/
- https://www.oracle.com/cloud/free/
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- https://www.hetzner.com/european-cloud/
