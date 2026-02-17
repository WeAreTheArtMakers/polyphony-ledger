# Production Reverse Proxy

This project uses Caddy in `docker-compose.prod.yml` to expose:
- `apppoly.wearetheartmakers.com` -> frontend
- `apipoly.wearetheartmakers.com` -> backend
- `obspoly.wearetheartmakers.com` -> Grafana (basic auth required)
- `tracepoly.wearetheartmakers.com` -> Jaeger (basic auth required)

Generate password hashes:

```bash
docker run --rm caddy:2.9.1-alpine caddy hash-password --plaintext 'StrongPasswordHere'
```

Set the resulting hash into `.env.prod` as `OBS_AUTH_HASH` and `TRACE_AUTH_HASH`.
