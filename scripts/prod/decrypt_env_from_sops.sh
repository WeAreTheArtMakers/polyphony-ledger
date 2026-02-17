#!/usr/bin/env bash
set -euo pipefail

ENC_FILE="${1:-infra/secrets/sops/prod.env.enc}"
OUT_FILE="${2:-.env.prod}"

if ! command -v sops >/dev/null 2>&1; then
  echo "sops is required but not installed" >&2
  exit 1
fi

if [[ ! -f "$ENC_FILE" ]]; then
  echo "encrypted env file not found: $ENC_FILE" >&2
  exit 1
fi

sops --decrypt "$ENC_FILE" > "$OUT_FILE"
chmod 600 "$OUT_FILE"
echo "wrote $OUT_FILE"
