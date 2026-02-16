from __future__ import annotations

from fastapi import APIRouter, Query

from app.db.session import get_pg_pool

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("/recent")
async def recent_ledger(limit: int = Query(default=100, ge=1, le=500)) -> list[dict]:
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT entry_id, tx_id::text, workspace_id, account_id, side, asset,
                   amount::text, correlation_id, occurred_at, created_at
            FROM ledger_entries
            ORDER BY entry_id DESC
            LIMIT $1
            """,
            limit,
        )
    return [dict(r) for r in rows]


@router.get("/batches")
async def recent_batches(limit: int = Query(default=50, ge=1, le=300)) -> list[dict]:
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
              tx_id::text,
              workspace_id,
              MAX(created_at) AS created_at,
              COUNT(*) AS entries,
              SUM(CASE WHEN side = 'debit' THEN amount ELSE 0 END)::text AS total_debit,
              SUM(CASE WHEN side = 'credit' THEN amount ELSE 0 END)::text AS total_credit
            FROM ledger_entries
            GROUP BY tx_id, workspace_id
            ORDER BY MAX(created_at) DESC
            LIMIT $1
            """,
            limit,
        )
    return [dict(r) for r in rows]


@router.get("/kpis")
async def ledger_kpis() -> dict[str, object]:
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        tx_count = await conn.fetchval("SELECT COUNT(*) FROM ledger_transactions")
        entry_count = await conn.fetchval("SELECT COUNT(*) FROM ledger_entries")
        volume_24h = await conn.fetchval(
            """
            SELECT COALESCE(SUM(amount), 0)::text
            FROM ledger_entries
            WHERE occurred_at >= NOW() - INTERVAL '24 hours'
            """
        )
        accounts = await conn.fetchval("SELECT COUNT(DISTINCT account_id) FROM ledger_entries")

    return {
        "tx_count": int(tx_count),
        "entry_count": int(entry_count),
        "volume_24h": str(volume_24h),
        "distinct_accounts": int(accounts),
    }
