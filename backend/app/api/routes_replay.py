from __future__ import annotations

from fastapi import APIRouter

from app.db.session import get_pg_pool
from app.services.replay import replay_balances_from_ledger

router = APIRouter(prefix="/replay", tags=["replay"])


@router.post("/from-ledger")
async def replay_from_ledger() -> dict[str, object]:
    pool = get_pg_pool()
    summary = await replay_balances_from_ledger(pool)
    return {"status": "ok", "summary": summary}
