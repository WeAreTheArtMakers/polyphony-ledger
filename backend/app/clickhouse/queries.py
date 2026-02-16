from __future__ import annotations

from typing import Any

from app.clickhouse.client import get_clickhouse_client


def _rows_to_dicts(column_names: list[str], rows: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    return [dict(zip(column_names, row)) for row in rows]


def query_volume_per_asset(minutes: int, workspace_id: str) -> list[dict[str, Any]]:
    client = get_clickhouse_client()
    result = client.query(
        """
        SELECT
          bucket,
          asset,
          sum(volume) AS volume
        FROM polyphony.volume_per_asset_1m
        WHERE workspace_id = %(workspace_id)s
          AND bucket >= now() - toIntervalMinute(%(minutes)s)
        GROUP BY bucket, asset
        ORDER BY bucket ASC, asset ASC
        """,
        parameters={"workspace_id": workspace_id, "minutes": minutes},
    )
    return _rows_to_dicts(result.column_names, result.result_rows)


def query_netflow(minutes: int, workspace_id: str, account_id: str) -> list[dict[str, Any]]:
    client = get_clickhouse_client()
    result = client.query(
        """
        SELECT
          bucket,
          asset,
          sum(netflow) AS netflow
        FROM polyphony.netflow_per_account_1m
        WHERE workspace_id = %(workspace_id)s
          AND account_id = %(account_id)s
          AND bucket >= now() - toIntervalMinute(%(minutes)s)
        GROUP BY bucket, asset
        ORDER BY bucket ASC, asset ASC
        """,
        parameters={
            "workspace_id": workspace_id,
            "account_id": account_id,
            "minutes": minutes,
        },
    )
    return _rows_to_dicts(result.column_names, result.result_rows)


def query_top_accounts(minutes: int, workspace_id: str, asset: str) -> list[dict[str, Any]]:
    client = get_clickhouse_client()
    result = client.query(
        """
        SELECT
          account_id,
          sum(netflow) AS netflow
        FROM polyphony.top_accounts_5m
        WHERE workspace_id = %(workspace_id)s
          AND asset = %(asset)s
          AND bucket >= now() - toIntervalMinute(%(minutes)s)
        GROUP BY account_id
        ORDER BY abs(netflow) DESC
        LIMIT 10
        """,
        parameters={
            "workspace_id": workspace_id,
            "asset": asset,
            "minutes": minutes,
        },
    )
    return _rows_to_dicts(result.column_names, result.result_rows)
