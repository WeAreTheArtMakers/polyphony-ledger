from __future__ import annotations

import asyncpg


async def mark_processed(conn: asyncpg.Connection, consumer_name: str, event_id: str) -> bool:
    row = await conn.fetchrow(
        """
        INSERT INTO processed_events (consumer_name, event_id)
        VALUES ($1, $2)
        ON CONFLICT (consumer_name, event_id) DO NOTHING
        RETURNING event_id
        """,
        consumer_name,
        event_id,
    )
    return row is not None
