# VPS Olmadan Guvenli Canli Demo (Cloudflare Tunnel + Docker Compose)

Bu runbook, Polyphony Ledger'i VPS kiralamadan internette yayinlamak icin en dusuk maliyetli yoldur.

## Bu kurulum ne saglar

- Full stack yerel makinede Docker Compose ile calisir.
- HTTPS endpoint'ler Cloudflare Tunnel uzerinden yayinlanir.
- Container portlari makinede `127.0.0.1` ile sinirlanir.
- Gozlemlenebilirlik endpoint'leri (`obspoly`, `tracepoly`) edge tarafinda erisim kontrolune alinabilir.

## On kosullar

1. Docker Desktop calisir durumda olmali.
2. Cloudflare hesabi ve Zero Trust aktif olmali.
3. Domain Cloudflare DNS'te yonetiliyor olmali (veya alt zone delegation yapilmis olmali).
4. Repo localde klonlanmis olmali.

## Adim adim checklist

1. Cloudflare Zero Trust uzerinde named tunnel olustur.
2. Tunnel icine 4 adet public hostname tanimla:
   - `apppoly...` -> `http://frontend:3000`
   - `apipoly...` -> `http://backend:8000`
   - `obspoly...` -> `http://grafana:3000`
   - `tracepoly...` -> `http://jaeger:16686`
3. Ortam dosyasini hazirla:
   - `cp .env.tunnel.example .env.tunnel`
   - `CLOUDFLARE_TUNNEL_TOKEN` doldur
   - guclu `GRAFANA_ADMIN_PASSWORD` ata
4. Stack'i baslat:

```bash
docker compose --env-file .env.tunnel -f docker-compose.yml -f docker-compose.tunnel.yml up -d --build
```

5. Dogrulama:
   - `https://apppoly...`
   - `https://apipoly.../health`
   - `https://obspoly...` (erisim politikasi istemeli)
   - `https://tracepoly...` (erisim politikasi istemeli)

## Cloudflare Access politika tabani

Cloudflare Access tarafinda iki self-hosted uygulama tanimla:

1. `obspoly...` allow-list politikasi
2. `tracepoly...` allow-list politikasi

Ilk adim icin sadece kendi e-posta kimligine izin vermek yeterlidir.

## Onemli sinirlar

- Uptime yerel makinenin acik kalmasina baglidir.
- Makine uyku moduna gecerse canli linkler kapanir.
- Bu yontem portfolyo/demo icin uygundur, kesintisiz production icin degildir.

## Sertlestirme sirasi

1. Ilk smoke test icin gecici `AUTH_MODE=off`.
2. Sonra `AUTH_MODE=oidc` gecisi.
3. Ingest/governance endpointleri icin write scope ayrimi.
4. Gozlemlenebilirlik endpointlerini Cloudflare Access arkasinda tut.
