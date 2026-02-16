from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any


def build_double_entries(
    tx_id: str,
    workspace_id: str,
    payer_account: str,
    payee_account: str,
    asset: str,
    amount: Decimal,
    correlation_id: str,
    occurred_at,
) -> list[dict[str, Any]]:
    return [
        {
            "tx_id": tx_id,
            "workspace_id": workspace_id,
            "account_id": payer_account,
            "side": "credit",
            "asset": asset,
            "amount": amount,
            "correlation_id": correlation_id,
            "occurred_at": occurred_at,
        },
        {
            "tx_id": tx_id,
            "workspace_id": workspace_id,
            "account_id": payee_account,
            "side": "debit",
            "asset": asset,
            "amount": amount,
            "correlation_id": correlation_id,
            "occurred_at": occurred_at,
        },
    ]


def build_batch_payload(
    tx_id: str,
    event_id: str,
    correlation_id: str,
    workspace_id: str,
    occurred_at,
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "batch_id": str(uuid.uuid4()),
        "tx_id": tx_id,
        "event_id": event_id,
        "correlation_id": correlation_id,
        "workspace_id": workspace_id,
        "created_at": occurred_at,
        "entries": entries,
    }
