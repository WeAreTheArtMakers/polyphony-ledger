from __future__ import annotations

from fastapi import APIRouter, Request

from app.authz import enforce_roles
from app.db.session import get_pg_pool
from app.services.replay import replay_balances_from_ledger

router = APIRouter(prefix="/replay", tags=["replay"])


@router.post("/from-ledger")
async def replay_from_ledger(request: Request) -> dict[str, object]:
    enforce_roles(request=request, allowed_roles={"admin", "owner"})
    pool = get_pg_pool()
    summary = await replay_balances_from_ledger(pool)
    return {"status": "ok", "summary": summary}
