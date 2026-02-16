from __future__ import annotations

import asyncpg

from app.tracing import get_tracer

tracer = get_tracer(__name__)


async def replay_balances_from_ledger(pool: asyncpg.Pool) -> dict[str, int]:
    async with pool.acquire() as conn:
        async with conn.transaction():
            with tracer.start_as_current_span("replay.truncate_balances"):
                await conn.execute("TRUNCATE TABLE account_balances")

            with tracer.start_as_current_span("replay.rebuild_balances"):
                inserted = await conn.execute(
                    """
                    INSERT INTO account_balances (workspace_id, account_id, asset, balance, updated_at)
                    SELECT
                      workspace_id,
                      account_id,
                      asset,
                      SUM(CASE WHEN side = 'debit' THEN amount ELSE -amount END) AS balance,
                      NOW()
                    FROM ledger_entries
                    GROUP BY workspace_id, account_id, asset
                    """
                )

            ledger_count = await conn.fetchval("SELECT COUNT(*) FROM ledger_entries")
            balance_count = await conn.fetchval("SELECT COUNT(*) FROM account_balances")

    return {
        "ledger_entry_count": int(ledger_count),
        "balances_count": int(balance_count),
        "insert_result": inserted,
    }
