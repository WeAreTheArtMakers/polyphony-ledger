# 14 - Domain/Subdomain Uzerinden Yayin Runbook

Bu runbook, elindeki domain ile projeyi subdomain'de canli gostermek icindir.

## Onerilen Subdomain Yapisi

- app.domainin.com -> frontend
- api.domainin.com -> backend
- obs.domainin.com -> Grafana (opsiyonel)
- trace.domainin.com -> Jaeger (opsiyonel)

## 1) Sunucu Hazirligi

- Ubuntu 22.04+
- Docker + Docker Compose
- firewall (80/443 acik)

## 2) DNS Ayari

- A kayitlari ile subdomainleri sunucu IP'sine yonlendir

## 3) Reverse Proxy

- Caddy veya Nginx ile TLS terminate et
- app -> frontend:3000
- api -> backend:8000
- obs/trace'i basic auth veya IP whitelist ile koru

## 4) Production Compose Prensibi

- public acik portlari azalt
- sadece proxy uzerinden erisim ver
- persistent volume + backup zorunlu

## 5) Guvenlik Kontrolleri

- default sifreleri degistir (Grafana dahil)
- rate limit + fail2ban/WAF
- gizli anahtarlar `.env` yerine secret store

## 6) CV ve Satis icin Demo Hazirlik

- root path'i `/sales` ac
- canli demo scriptini sabitle
- 5 dakikada "ingest -> ledger -> analytics -> trace" akisini gosterecek notlar hazirla
