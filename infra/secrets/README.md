# Secrets Management (SOPS / Vault)

This repository keeps production secret values out of git.

## Option A: SOPS
1. Install `sops` and configure an age recipient in `infra/secrets/sops/.sops.yaml`.
2. Prepare `.env.prod` from `.env.prod.example`.
3. Encrypt: `sops --encrypt --in-place .env.prod`.
4. Move encrypted file to `infra/secrets/sops/prod.env.enc`.
5. Decrypt for deployment: `scripts/prod/decrypt_env_from_sops.sh infra/secrets/sops/prod.env.enc .env.prod`.

## Option B: Vault
1. Store key-value pairs under Vault path `secret/data/polyphony/prod`.
2. Login with `vault login` (or Vault Agent).
3. Render env file: `scripts/prod/render_env_from_vault.sh secret/data/polyphony/prod .env.prod`.

## Production compose
Run with:
`docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build`
