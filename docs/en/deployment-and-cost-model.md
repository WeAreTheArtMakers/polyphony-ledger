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

This public document uses a commercial proposal model instead of exposing raw infrastructure cost lines.

## Commercial Proposal Structure (Public)

Total proposal consists of:

1. One-time implementation fee
2. Monthly platform fee

## Pricing Variables

Final pricing is scoped by:

- throughput profile (monthly tx volume and peak TPS)
- retention policy (logs/metrics/traces retention windows)
- availability target (uptime and failover level)
- integration scope (SSO, RBAC, governance, reporting)

## Reference Package Shapes

- Foundation: single-node live environment with baseline observability
- Growth: controlled pilot topology with advanced alerting and active governance
- Enterprise: multi-node architecture with high-availability and hardened controls

Raw infrastructure cost details are intentionally handled in internal pricing models after technical discovery.
