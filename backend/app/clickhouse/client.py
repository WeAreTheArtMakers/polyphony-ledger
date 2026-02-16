from __future__ import annotations

import clickhouse_connect

from app.config import get_settings

_client = None


def get_clickhouse_client():
    global _client
    if _client is None:
        settings = get_settings()
        _client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            username=settings.clickhouse_username,
            password=settings.clickhouse_password,
            database=settings.clickhouse_database,
        )
    return _client


def close_clickhouse_client() -> None:
    global _client
    if _client is not None:
        _client.close()
    _client = None
