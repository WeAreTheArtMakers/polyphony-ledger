from __future__ import annotations

from decimal import Decimal


def signed_amount(side: str, amount: Decimal) -> Decimal:
    if side == "debit":
        return amount
    if side == "credit":
        return amount * Decimal("-1")
    raise ValueError(f"unknown side: {side}")
