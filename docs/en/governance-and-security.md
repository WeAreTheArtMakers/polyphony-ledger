# Governance and Security

## Current Governance Capabilities

- role-based guards (`viewer`, `operator`, `admin`, `owner`)
- tenant quota controls for ingest operations
- usage metering endpoints per workspace
- OIDC token validation mode (Auth0/Keycloak compatible) with legacy header mode fallback

## Security and Operations Baseline

- immutable financial records
- structured logs and trace-linked failures
- DLQ isolation with redacted payload handling
- endpoint-level health/readiness checks

## Enterprise Hardening Path

- OIDC/SAML integration at gateway or API layer
- fine-grained policy expansion by role and tenant
- key rotation and secret manager integration
- disaster recovery drills and backup validation routines
