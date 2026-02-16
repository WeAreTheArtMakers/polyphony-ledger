from __future__ import annotations

from fastapi import APIRouter, Query

from app.db.session import get_pg_pool

router = APIRouter(prefix="/balances", tags=["balances"])


@router.get("")
async def list_balances(
    workspace_id: str = Query(default="default"),
    limit: int = Query(default=200, ge=1, le=2000),
) -> list[dict]:
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT workspace_id, account_id, asset, balance::text, updated_at
            FROM account_balances
            WHERE workspace_id = $1
            ORDER BY ABS(balance) DESC, account_id ASC
            LIMIT $2
            """,
            workspace_id,
            limit,
        )
    return [dict(r) for r in rows]


@router.get("/{account_id}")
async def account_balances(account_id: str, workspace_id: str = Query(default="default")) -> list[dict]:
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT workspace_id, account_id, asset, balance::text, updated_at
            FROM account_balances
            WHERE workspace_id = $1 AND account_id = $2
            ORDER BY asset ASC
            """,
            workspace_id,
            account_id,
        )
    return [dict(r) for r in rows]
