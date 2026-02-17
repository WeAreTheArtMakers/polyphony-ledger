from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

import asyncpg

from app.config import get_settings
from app.metrics import (
    WORKSPACE_QUOTA_REJECTIONS_TOTAL,
    WORKSPACE_USAGE_CONSUMED_TOTAL,
    WORKSPACE_USAGE_REFUNDED_TOTAL,
)


class QuotaExceededError(RuntimeError):
    def __init__(self, workspace_id: str, current: int, quota: int) -> None:
        super().__init__(f"workspace quota exceeded workspace_id={workspace_id} current={current} quota={quota}")
        self.workspace_id = workspace_id
        self.current = current
        self.quota = quota


@dataclass(frozen=True)
class WorkspaceQuota:
    workspace_id: str
    monthly_tx_quota: int
    is_active: bool
    tx_ingested_this_month: int
    period_month: date

    def to_dict(self) -> dict[str, object]:
        return {
            "workspace_id": self.workspace_id,
            "monthly_tx_quota": self.monthly_tx_quota,
            "is_active": self.is_active,
            "tx_ingested_this_month": self.tx_ingested_this_month,
            "period_month": self.period_month.isoformat(),
        }


def current_period_month() -> date:
    today = datetime.now(timezone.utc).date()
    return date(today.year, today.month, 1)


async def _ensure_workspace_records(conn: asyncpg.Connection, workspace_id: str) -> None:
    settings = get_settings()
    period_month = current_period_month()
    await conn.execute(
        """
        INSERT INTO workspace_quotas (workspace_id, monthly_tx_quota, is_active)
        VALUES ($1, $2, TRUE)
        ON CONFLICT (workspace_id) DO NOTHING
        """,
        workspace_id,
        settings.default_workspace_monthly_tx_quota,
    )
    await conn.execute(
        """
        INSERT INTO workspace_usage (workspace_id, period_month, tx_ingested)
        VALUES ($1, $2, 0)
        ON CONFLICT (workspace_id, period_month) DO NOTHING
        """,
        workspace_id,
        period_month,
    )


async def read_workspace_quota(pool: asyncpg.Pool, workspace_id: str) -> WorkspaceQuota:
    async with pool.acquire() as conn:
        await _ensure_workspace_records(conn, workspace_id)
        period_month = current_period_month()
        row = await conn.fetchrow(
            """
            SELECT q.workspace_id,
                   q.monthly_tx_quota,
                   q.is_active,
                   COALESCE(u.tx_ingested, 0) AS tx_ingested_this_month,
                   $2::DATE AS period_month
            FROM workspace_quotas q
            LEFT JOIN workspace_usage u
              ON u.workspace_id = q.workspace_id
             AND u.period_month = $2::DATE
            WHERE q.workspace_id = $1
            """,
            workspace_id,
            period_month,
        )
        if row is None:
            raise RuntimeError(f"failed to read quota for workspace_id={workspace_id}")
    return WorkspaceQuota(
        workspace_id=str(row["workspace_id"]),
        monthly_tx_quota=int(row["monthly_tx_quota"]),
        is_active=bool(row["is_active"]),
        tx_ingested_this_month=int(row["tx_ingested_this_month"]),
        period_month=row["period_month"],
    )


async def upsert_workspace_quota(
    pool: asyncpg.Pool,
    workspace_id: str,
    monthly_tx_quota: int,
    is_active: bool,
) -> WorkspaceQuota:
    period_month = current_period_month()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO workspace_quotas (workspace_id, monthly_tx_quota, is_active)
                VALUES ($1, $2, $3)
                ON CONFLICT (workspace_id)
                DO UPDATE SET
                    monthly_tx_quota = EXCLUDED.monthly_tx_quota,
                    is_active = EXCLUDED.is_active,
                    updated_at = NOW()
                """,
                workspace_id,
                monthly_tx_quota,
                is_active,
            )
            await conn.execute(
                """
                INSERT INTO workspace_usage (workspace_id, period_month, tx_ingested)
                VALUES ($1, $2, 0)
                ON CONFLICT (workspace_id, period_month) DO NOTHING
                """,
                workspace_id,
                period_month,
            )
    return await read_workspace_quota(pool=pool, workspace_id=workspace_id)


async def consume_workspace_quota(pool: asyncpg.Pool, workspace_id: str, units: int = 1) -> WorkspaceQuota:
    if units <= 0:
        raise ValueError(f"units must be positive, got={units}")
    period_month = current_period_month()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _ensure_workspace_records(conn, workspace_id)

            row = await conn.fetchrow(
                """
                SELECT q.monthly_tx_quota,
                       q.is_active,
                       COALESCE(u.tx_ingested, 0) AS tx_ingested
                FROM workspace_quotas q
                JOIN workspace_usage u
                  ON u.workspace_id = q.workspace_id
                 AND u.period_month = $2::DATE
                WHERE q.workspace_id = $1
                FOR UPDATE
                """,
                workspace_id,
                period_month,
            )
            if row is None:
                raise RuntimeError(f"quota state not found for workspace_id={workspace_id}")

            quota = int(row["monthly_tx_quota"])
            is_active = bool(row["is_active"])
            current = int(row["tx_ingested"])

            if not is_active:
                WORKSPACE_QUOTA_REJECTIONS_TOTAL.labels(workspace_id=workspace_id, reason="workspace_inactive").inc()
                raise QuotaExceededError(workspace_id=workspace_id, current=current, quota=quota)

            if current + units > quota:
                WORKSPACE_QUOTA_REJECTIONS_TOTAL.labels(workspace_id=workspace_id, reason="quota_exceeded").inc()
                raise QuotaExceededError(workspace_id=workspace_id, current=current, quota=quota)

            await conn.execute(
                """
                UPDATE workspace_usage
                   SET tx_ingested = tx_ingested + $3,
                       updated_at = NOW()
                 WHERE workspace_id = $1
                   AND period_month = $2::DATE
                """,
                workspace_id,
                period_month,
                units,
            )
            new_total = current + units

    WORKSPACE_USAGE_CONSUMED_TOTAL.labels(workspace_id=workspace_id).inc(units)
    return WorkspaceQuota(
        workspace_id=workspace_id,
        monthly_tx_quota=quota,
        is_active=is_active,
        tx_ingested_this_month=new_total,
        period_month=period_month,
    )


async def refund_workspace_quota(
    pool: asyncpg.Pool,
    workspace_id: str,
    units: int = 1,
    reason: str = "adjustment",
) -> WorkspaceQuota:
    if units <= 0:
        raise ValueError(f"units must be positive, got={units}")
    period_month = current_period_month()
    refunded_units = 0

    async with pool.acquire() as conn:
        async with conn.transaction():
            await _ensure_workspace_records(conn, workspace_id)

            row = await conn.fetchrow(
                """
                SELECT q.monthly_tx_quota,
                       q.is_active,
                       COALESCE(u.tx_ingested, 0) AS tx_ingested
                FROM workspace_quotas q
                JOIN workspace_usage u
                  ON u.workspace_id = q.workspace_id
                 AND u.period_month = $2::DATE
                WHERE q.workspace_id = $1
                FOR UPDATE
                """,
                workspace_id,
                period_month,
            )
            if row is None:
                raise RuntimeError(f"quota state not found for workspace_id={workspace_id}")

            quota = int(row["monthly_tx_quota"])
            is_active = bool(row["is_active"])
            current = int(row["tx_ingested"])
            refunded_units = min(units, current)
            new_total = current - refunded_units

            if refunded_units > 0:
                await conn.execute(
                    """
                    UPDATE workspace_usage
                       SET tx_ingested = $3,
                           updated_at = NOW()
                     WHERE workspace_id = $1
                       AND period_month = $2::DATE
                    """,
                    workspace_id,
                    period_month,
                    new_total,
                )

    if refunded_units > 0:
        WORKSPACE_USAGE_REFUNDED_TOTAL.labels(workspace_id=workspace_id, reason=reason).inc(refunded_units)
    return WorkspaceQuota(
        workspace_id=workspace_id,
        monthly_tx_quota=quota,
        is_active=is_active,
        tx_ingested_this_month=new_total,
        period_month=period_month,
    )


async def list_workspace_usage(pool: asyncpg.Pool, workspace_id: str, months: int = 6) -> list[dict[str, object]]:
    bounded_months = max(1, min(months, 24))
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT workspace_id, period_month, tx_ingested, updated_at
            FROM workspace_usage
            WHERE workspace_id = $1
            ORDER BY period_month DESC
            LIMIT $2
            """,
            workspace_id,
            bounded_months,
        )
    return [
        {
            "workspace_id": str(row["workspace_id"]),
            "period_month": row["period_month"].isoformat(),
            "tx_ingested": int(row["tx_ingested"]),
            "updated_at": row["updated_at"].isoformat(),
        }
        for row in rows
    ]
