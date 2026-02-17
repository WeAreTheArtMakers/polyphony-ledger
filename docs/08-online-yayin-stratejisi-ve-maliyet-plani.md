# 08 - Online Yayın Stratejisi ve Maliyet Planı

## Grafana Login Notu

Varsayılan giriş:

- kullanıcı adı: `admin`
- parola: `admin`

Eğer tarayıcı otomatik doldurma farklı bir kullanıcı adı/parola yazıyorsa giriş başarısız olur.

## "Free Plan" Gerçeği

Bu proje; Kafka uyumlu broker, Postgres, ClickHouse, Grafana, Prometheus, Jaeger, API ve worker’ları birlikte içerdiği için tam kapsamlı "sürekli çalışan" ücretsiz planlarda eksiksiz çalıştırmak pratikte zordur.

## Önerilen Yayın Modeli

## 1) Demo/PoC için en güvenli yol

- Tek bir VPS (8 vCPU / 16 GB RAM) üzerinde Docker Compose
- Domain + reverse proxy (Caddy/Nginx)
- TLS (Let’s Encrypt)

## 2) Ücretsiz gösterim için alternatif

- Lokal ortam + tünel (Cloudflare Tunnel gibi) ile kısa süreli canlı demo
- Kalıcı prod için önerilmez

## 3) Hibrit yaklaşım

- Ağır stateful servisler (Redpanda, Postgres, ClickHouse) VPS’te
- Frontend + API daha esnek platformda

## Kaynak Planı (Başlangıç)

- CPU: 8 vCPU
- RAM: 16 GB
- Disk: NVMe 200 GB+

## Ölçekleme Prensibi

1. Önce observability metriklerinden darboğazı tespit et.
2. Sonra bileşen bazında (broker/worker/DB) ölçekle.
3. En son mimariyi böl (multi-node / managed geçiş).
