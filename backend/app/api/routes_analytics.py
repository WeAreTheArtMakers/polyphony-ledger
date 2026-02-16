from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.analytics import get_netflow, get_top_accounts, get_volume_per_asset

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/volume-per-asset")
async def volume_per_asset(
    minutes: int = Query(default=60, ge=1, le=24 * 60),
    workspace_id: str = Query(default="default"),
) -> dict[str, object]:
    rows = get_volume_per_asset(minutes=minutes, workspace_id=workspace_id)
    return {"rows": rows, "minutes": minutes, "workspace_id": workspace_id}


@router.get("/netflow")
async def netflow(
    account_id: str,
    minutes: int = Query(default=60, ge=1, le=24 * 60),
    workspace_id: str = Query(default="default"),
) -> dict[str, object]:
    rows = get_netflow(minutes=minutes, workspace_id=workspace_id, account_id=account_id)
    return {
        "rows": rows,
        "minutes": minutes,
        "workspace_id": workspace_id,
        "account_id": account_id,
    }


@router.get("/top-accounts")
async def top_accounts(
    asset: str = Query(default="USDT"),
    minutes: int = Query(default=60, ge=1, le=24 * 60),
    workspace_id: str = Query(default="default"),
) -> dict[str, object]:
    rows = get_top_accounts(minutes=minutes, workspace_id=workspace_id, asset=asset.upper())
    return {
        "rows": rows,
        "minutes": minutes,
        "workspace_id": workspace_id,
        "asset": asset.upper(),
    }
