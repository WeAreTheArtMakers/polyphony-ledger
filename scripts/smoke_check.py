#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from typing import Any


API_BASE = os.getenv("API_BASE", "http://localhost:8000").rstrip("/")
SMOKE_TIMEOUT_SECONDS = float(os.getenv("SMOKE_TIMEOUT_SECONDS", "90"))
POLL_INTERVAL_SECONDS = float(os.getenv("SMOKE_POLL_INTERVAL_SECONDS", "1"))


def _request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    command = [
        "curl",
        "-sS",
        "-X",
        method,
        f"{API_BASE}{path}",
        "-H",
        "content-type: application/json",
        "-w",
        "\n%{http_code}",
    ]
    if payload is not None:
        command.extend(["-d", json.dumps(payload, separators=(",", ":"))])

    result = subprocess.run(command, check=True, capture_output=True, text=True)
    body, code = result.stdout.rsplit("\n", 1)
    status_code = int(code.strip())
    if status_code < 200 or status_code >= 300:
        raise RuntimeError(f"{method} {path} failed with {status_code}: {body}")
    return json.loads(body) if body else None


def _wait_until(label: str, predicate, timeout_seconds: float = SMOKE_TIMEOUT_SECONDS) -> Any:
    started = time.monotonic()
    last_value: Any = None
    while time.monotonic() - started < timeout_seconds:
        try:
            last_value = predicate()
        except Exception as exc:
            last_value = f"error: {exc}"
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        if last_value:
            return last_value
        time.sleep(POLL_INTERVAL_SECONDS)
    raise TimeoutError(f"Timed out waiting for {label}. Last value: {last_value!r}")


def main() -> int:
    health = _request_json("GET", "/health")
    if health.get("status") != "ok":
        raise RuntimeError(f"Health check failed: {health}")

    event_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    payload = {
        "payer_account": "acct_smoke_payer",
        "payee_account": "acct_smoke_payee",
        "asset": "USDT",
        "amount": 12.34,
        "workspace_id": "smoke",
        "payment_memo": "smoke-check",
        "client_id": "smoke-check",
        "event_id": event_id,
        "correlation_id": correlation_id,
    }
    ingest = _request_json("POST", "/tx/ingest", payload)
    if ingest.get("event_id") != event_id:
        raise RuntimeError(f"Unexpected ingest response: {ingest}")

    def validated_seen() -> bool:
        rows = _request_json("GET", "/tx/recent/validated?limit=200")
        return any(row.get("event_id") == event_id for row in rows)

    _wait_until("validated transaction", validated_seen)

    def ledger_seen() -> bool:
        rows = _request_json("GET", "/ledger/recent?limit=200")
        return any(row.get("correlation_id") == correlation_id for row in rows)

    _wait_until("ledger entry visibility", ledger_seen)

    def analytics_seen() -> bool:
        data = _request_json("GET", "/analytics/volume-per-asset?minutes=60&workspace_id=smoke")
        rows = data.get("rows", [])
        return len(rows) > 0

    _wait_until("analytics materialization", analytics_seen)

    replay = _request_json("POST", "/replay/from-ledger")
    if replay.get("status") != "ok":
        raise RuntimeError(f"Replay response was not ok: {replay}")

    print(
        json.dumps(
            {
                "status": "ok",
                "event_id": event_id,
                "correlation_id": correlation_id,
                "checked": ["/health", "/tx/ingest", "/ledger/recent", "/analytics/volume-per-asset", "/replay/from-ledger"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"SMOKE_CHECK_FAILED: {exc}", file=sys.stderr)
        raise
