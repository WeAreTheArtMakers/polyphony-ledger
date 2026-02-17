# No-VPS Secure Live Demo (Cloudflare Tunnel + Docker Compose)

This runbook is the lowest-cost path for publishing Polyphony Ledger online without renting a VPS.

## What this setup does

- Runs the full stack on your own machine with Docker Compose.
- Publishes HTTPS endpoints through Cloudflare Tunnel.
- Keeps container ports bound to `127.0.0.1` on your machine.
- Adds edge access control for observability routes (`obspoly`, `tracepoly`).

## Prerequisites

1. Docker Desktop is running on your machine.
2. A Cloudflare account with Zero Trust enabled.
3. Your domain is managed by Cloudflare DNS, or a delegated sub-zone is managed there.
4. Repository cloned locally.

## Step-by-step checklist

1. Create a named tunnel in Cloudflare Zero Trust.
2. Add 4 public hostnames to that tunnel:
   - `apppoly...` -> `http://frontend:3000`
   - `apipoly...` -> `http://backend:8000`
   - `obspoly...` -> `http://grafana:3000`
   - `tracepoly...` -> `http://jaeger:16686`
3. Copy and fill environment file:
   - `cp .env.tunnel.example .env.tunnel`
   - set `CLOUDFLARE_TUNNEL_TOKEN`
   - set strong `GRAFANA_ADMIN_PASSWORD`
4. Start the stack:

```bash
docker compose --env-file .env.tunnel -f docker-compose.yml -f docker-compose.tunnel.yml up -d --build
```

5. Verify:
   - `https://apppoly...`
   - `https://apipoly.../health`
   - `https://obspoly...` (should require access policy)
   - `https://tracepoly...` (should require access policy)

## Cloudflare Access policy baseline

Create 2 self-hosted applications in Cloudflare Access:

1. `obspoly...` allow-list policy
2. `tracepoly...` allow-list policy

Recommended first policy: allow only your email identity.

## Important limitations

- Availability depends on your machine uptime and internet stability.
- If your machine sleeps, the public demo goes down.
- This is ideal for portfolio/demo usage, not for always-on production.

## Hardening sequence

1. Keep `AUTH_MODE=off` only for first smoke test.
2. Switch to `AUTH_MODE=oidc`.
3. Enable write scopes for ingest/governance routes.
4. Keep observability behind Cloudflare Access.
