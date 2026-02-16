from __future__ import annotations

from app.clickhouse.queries import query_netflow, query_top_accounts, query_volume_per_asset


def get_volume_per_asset(minutes: int, workspace_id: str) -> list[dict]:
    return query_volume_per_asset(minutes=minutes, workspace_id=workspace_id)


def get_netflow(minutes: int, workspace_id: str, account_id: str) -> list[dict]:
    return query_netflow(minutes=minutes, workspace_id=workspace_id, account_id=account_id)


def get_top_accounts(minutes: int, workspace_id: str, asset: str) -> list[dict]:
    return query_top_accounts(minutes=minutes, workspace_id=workspace_id, asset=asset)
