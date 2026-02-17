#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
import uuid
from typing import Any


API_BASE = os.getenv("API_BASE", "http://localhost:8000").rstrip("/")
E2E_TIMEOUT_SECONDS = float(os.getenv("E2E_TIMEOUT_SECONDS", "120"))
POLL_INTERVAL_SECONDS = float(os.getenv("E2E_POLL_INTERVAL_SECONDS", "1"))
COMPOSE_CMD = shlex.split(os.getenv("COMPOSE_CMD", "docker compose"))


def _compose_exec(service: str, *args: str) -> str:
    cmd = [*COMPOSE_CMD, "exec", "-T", service, *args]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


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


def _wait_until(label: str, predicate, timeout_seconds: float = E2E_TIMEOUT_SECONDS) -> Any:
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


def _topic_high_watermark_sum(topic: str) -> int:
    output = _compose_exec("redpanda", "rpk", "topic", "describe", topic, "-p")
    total = 0
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 6 and parts[0].isdigit():
            total += int(parts[5])
    return total


def _psql_scalar(sql: str) -> str:
    return _compose_exec("postgres", "psql", "-U", "polyphony", "-d", "polyphony", "-t", "-A", "-c", sql).strip()


def _clickhouse_scalar(sql: str) -> str:
    return _compose_exec(
        "clickhouse",
        "clickhouse-client",
        "--user",
        "default",
        "--password",
        "polyphony",
        "--query",
        sql,
    ).strip()


def main() -> int:
    for path in ("/health", "/ledger/kpis"):
        _request_json("GET", path)

    topic_before = {
        "tx_raw": _topic_high_watermark_sum("tx_raw"),
        "tx_validated": _topic_high_watermark_sum("tx_validated"),
        "ledger_entry_batches": _topic_high_watermark_sum("ledger_entry_batches"),
    }

    event_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    workspace_id = "ci-e2e"
    payer = "acct_ci_payer"
    payee = "acct_ci_payee"

    ingest = _request_json(
        "POST",
        "/tx/ingest",
        {
            "payer_account": payer,
            "payee_account": payee,
            "asset": "USDT",
            "amount": 3.14,
            "workspace_id": workspace_id,
            "payment_memo": "ci-e2e-pipeline",
            "client_id": "ci-e2e",
            "event_id": event_id,
            "correlation_id": correlation_id,
        },
    )
    if ingest.get("status") != "accepted":
        raise RuntimeError(f"Ingest not accepted: {ingest}")

    for topic in ("tx_raw", "tx_validated", "ledger_entry_batches"):
        _wait_until(
            f"{topic} high watermark increment",
            lambda topic_name=topic: _topic_high_watermark_sum(topic_name) > topic_before[topic_name],
        )

    _wait_until(
        "events row persisted",
        lambda: int(_psql_scalar(f"SELECT count(*) FROM events WHERE event_id = '{event_id}'::uuid;")) >= 1,
    )

    tx_id = _wait_until(
        "ledger transaction creation",
        lambda: _psql_scalar(f"SELECT tx_id::text FROM ledger_transactions WHERE event_id = '{event_id}'::uuid LIMIT 1;"),
    )

    _wait_until(
        "outbox published",
        lambda: int(_psql_scalar(f"SELECT count(*) FROM outbox WHERE key = '{tx_id}' AND published_at IS NOT NULL;")) >= 1,
    )

    _wait_until(
        "balance projection update",
        lambda: int(
            _psql_scalar(
                "SELECT count(*) FROM account_balances "
                f"WHERE workspace_id = '{workspace_id}' AND asset = 'USDT' "
                f"AND account_id IN ('{payer}', '{payee}');"
            )
        )
        >= 2,
    )

    _wait_until(
        "clickhouse write",
        lambda: int(
            _clickhouse_scalar(
                "SELECT count() FROM polyphony.ledger_entries_raw "
                f"WHERE workspace_id = '{workspace_id}' AND event_id = '{event_id}';"
            )
        )
        >= 2,
    )

    _wait_until(
        "analytics rows available",
        lambda: len(_request_json("GET", f"/analytics/volume-per-asset?minutes=60&workspace_id={workspace_id}")["rows"]) > 0,
    )

    batches = _request_json("GET", "/ledger/batches?limit=200")
    if not any(row.get("tx_id") == tx_id for row in batches):
        raise RuntimeError(f"Expected tx_id {tx_id} in /ledger/batches response")

    print(
        json.dumps(
            {
                "status": "ok",
                "event_id": event_id,
                "correlation_id": correlation_id,
                "tx_id": tx_id,
                "topics_before": topic_before,
                "topics_after": {
                    "tx_raw": _topic_high_watermark_sum("tx_raw"),
                    "tx_validated": _topic_high_watermark_sum("tx_validated"),
                    "ledger_entry_batches": _topic_high_watermark_sum("ledger_entry_batches"),
                },
            }
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"E2E_PIPELINE_CHECK_FAILED: {exc}", file=sys.stderr)
        raise
