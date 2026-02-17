#!/usr/bin/env bash
set -euo pipefail

VAULT_PATH="${1:-secret/data/polyphony/prod}"
OUT_FILE="${2:-.env.prod}"

if ! command -v vault >/dev/null 2>&1; then
  echo "vault CLI is required but not installed" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required but not installed" >&2
  exit 1
fi

vault kv get -format=json "$VAULT_PATH" \
  | jq -r '.data.data | to_entries[] | "\(.key)=\(.value)"' > "$OUT_FILE"
chmod 600 "$OUT_FILE"
echo "wrote $OUT_FILE from $VAULT_PATH"
