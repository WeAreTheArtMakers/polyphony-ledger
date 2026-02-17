from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


class ValidationError(ValueError):
    pass


@dataclass(frozen=True)
class NormalizedTx:
    tx_id: str
    event_id: str
    correlation_id: str
    payer_account: str
    payee_account: str
    asset: str
    amount: Decimal
    occurred_at: datetime
    validation_version: str
    workspace_id: str
    payment_memo: str | None
    client_id: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "tx_id": self.tx_id,
            "event_id": self.event_id,
            "correlation_id": self.correlation_id,
            "payer_account": self.payer_account,
            "payee_account": self.payee_account,
            "asset": self.asset,
            "amount": self.amount,
            "occurred_at": self.occurred_at,
            "validation_version": self.validation_version,
            "workspace_id": self.workspace_id,
            "payment_memo": self.payment_memo,
            "client_id": self.client_id,
        }


def _normalize_account(account: str) -> str:
    return account.strip().lower()


def _canonical_uuid(value: str, field_name: str) -> str:
    try:
        return str(uuid.UUID(value))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a valid UUID") from exc


def normalize_and_validate(raw: dict[str, object], allowed_assets: set[str]) -> NormalizedTx:
    try:
        amount = Decimal(str(raw["amount"]))
    except (InvalidOperation, KeyError) as exc:
        raise ValidationError("invalid amount") from exc

    if amount <= 0:
        raise ValidationError("amount must be positive")

    payer = _normalize_account(str(raw.get("payer_account", "")))
    payee = _normalize_account(str(raw.get("payee_account", "")))
    if not payer or not payee:
        raise ValidationError("payer_account and payee_account are required")
    if payer == payee:
        raise ValidationError("payer_account and payee_account must differ")

    asset = str(raw.get("asset", "")).upper().strip()
    if asset not in allowed_assets:
        raise ValidationError(f"asset must be one of {sorted(allowed_assets)}")

    workspace_id = str(raw.get("workspace_id") or "default").strip() or "default"

    occurred_at_raw = raw.get("occurred_at")
    if isinstance(occurred_at_raw, datetime):
        occurred_at = occurred_at_raw
    else:
        raise ValidationError("occurred_at must be a datetime")

    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=timezone.utc)

    event_id = str(raw.get("event_id") or "")
    correlation_id = str(raw.get("correlation_id") or "")
    if not event_id or not correlation_id:
        raise ValidationError("event_id and correlation_id are required")
    event_id = _canonical_uuid(event_id, "event_id")

    tx_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{workspace_id}:{event_id}"))

    return NormalizedTx(
        tx_id=tx_id,
        event_id=event_id,
        correlation_id=correlation_id,
        payer_account=payer,
        payee_account=payee,
        asset=asset,
        amount=amount,
        occurred_at=occurred_at.astimezone(timezone.utc),
        validation_version="tx-validator-v2",
        workspace_id=workspace_id,
        payment_memo=str(raw.get("payment_memo")) if raw.get("payment_memo") else None,
        client_id=str(raw.get("client_id")) if raw.get("client_id") else None,
    )
