# Cloudflare Tunnel (No VPS Path)

This path is for running the full Docker Compose stack on your local machine and publishing selected routes securely through Cloudflare Tunnel.

## Why this path

- No VPS purchase required.
- No inbound port opening on your router.
- Public HTTPS URLs for portfolio/demo usage.
- Access control can be enforced at Cloudflare Access for observability routes.

## Compose command

```bash
cp .env.tunnel.example .env.tunnel
docker compose --env-file .env.tunnel -f docker-compose.yml -f docker-compose.tunnel.yml up -d --build
```

## Required tunnel hostnames

Create one named tunnel and map these hostnames:

- `apppoly...` -> `http://frontend:3000`
- `apipoly...` -> `http://backend:8000`
- `obspoly...` -> `http://grafana:3000`
- `tracepoly...` -> `http://jaeger:16686`

## Security baseline

- Keep `AUTH_MODE=off` only for first smoke test.
- Move to `AUTH_MODE=oidc` for protected write APIs.
- Enforce Cloudflare Access for `obspoly` and `tracepoly`.
- Use strong `GRAFANA_ADMIN_PASSWORD`.
- Keep `CLOUDFLARE_TUNNEL_TOKEN` secret and out of git.
