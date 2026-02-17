from __future__ import annotations

import asyncpg

from app.config import get_settings

_pool: asyncpg.Pool | None = None

_RUNTIME_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS workspace_quotas (
    workspace_id TEXT PRIMARY KEY,
    monthly_tx_quota BIGINT NOT NULL CHECK (monthly_tx_quota >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workspace_usage (
    workspace_id TEXT NOT NULL,
    period_month DATE NOT NULL,
    tx_ingested BIGINT NOT NULL DEFAULT 0 CHECK (tx_ingested >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (workspace_id, period_month),
    FOREIGN KEY (workspace_id) REFERENCES workspace_quotas(workspace_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS workspace_members (
    workspace_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('viewer', 'operator', 'admin', 'owner')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (workspace_id, subject_id),
    FOREIGN KEY (workspace_id) REFERENCES workspace_quotas(workspace_id) ON DELETE CASCADE
);
"""


async def init_pg_pool() -> asyncpg.Pool:
    global _pool
    if _pool is not None:
        return _pool
    settings = get_settings()
    _pool = await asyncpg.create_pool(
        dsn=settings.postgres_dsn,
        min_size=settings.postgres_min_pool,
        max_size=settings.postgres_max_pool,
        command_timeout=30,
    )
    async with _pool.acquire() as conn:
        await conn.execute(_RUNTIME_SCHEMA_SQL)
    return _pool


def get_pg_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Postgres pool is not initialized")
    return _pool


async def close_pg_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
    _pool = None
