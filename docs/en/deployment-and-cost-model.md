# Deployment and Cost Model

## Recommended Deployment Modes

## 1) Public Demo / Portfolio

- single VPS node
- full stack via Docker Compose
- reverse proxy + TLS + subdomain routing

## 2) Controlled Pilot

- split application and database responsibilities
- dedicated backup and retention strategy
- stricter monitoring and alert routing

## 3) Production

- multi-node topology
- explicit SLO/SLA operations
- hardened access and secrets management

## Cost Planning (Reference Bands)

- Demo tier: ~80 to 220 USD/month
- Pilot tier: ~250 to 700 USD/month
- Enterprise baseline: ~800 to 2500+ USD/month

Actual cost depends on throughput, retention windows, and availability targets.
