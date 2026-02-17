from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.authz import AuthContext, enforce_roles, resolve_auth_context
from app.config import get_settings
from app.db.session import get_pg_pool
from app.services.governance import list_workspace_usage, read_workspace_quota, upsert_workspace_quota

router = APIRouter(prefix="/governance", tags=["governance"])


class QuotaUpdateRequest(BaseModel):
    workspace_id: str = Field(..., min_length=1, max_length=64)
    monthly_tx_quota: int = Field(..., ge=0, le=1_000_000_000)
    is_active: bool = True


def _resolve_target_workspace(context: AuthContext, requested_workspace_id: str) -> str:
    target_workspace = requested_workspace_id.strip() or context.workspace_id
    settings = get_settings()
    if settings.auth_mode in {"header", "oidc"} and target_workspace != context.workspace_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "workspace_scope_violation",
                "request_workspace_id": target_workspace,
                "header_workspace_id": context.workspace_id,
            },
        )
    return target_workspace


@router.get("/me")
async def governance_me(request: Request) -> dict[str, str]:
    context = resolve_auth_context(request=request, workspace_fallback="default")
    return {
        "auth_mode": context.auth_mode,
        "subject_id": context.subject_id,
        "workspace_id": context.workspace_id,
        "role": context.role,
    }


@router.get("/quota")
async def governance_quota(
    request: Request,
    workspace_id: str = Query(default="", max_length=64),
) -> dict[str, object]:
    context = enforce_roles(request=request, allowed_roles={"viewer", "operator", "admin", "owner"})
    target_workspace = _resolve_target_workspace(context=context, requested_workspace_id=workspace_id)
    quota = await read_workspace_quota(pool=get_pg_pool(), workspace_id=target_workspace)
    return {"quota": quota.to_dict()}


@router.post("/quota")
async def governance_quota_update(request: Request, payload: QuotaUpdateRequest) -> dict[str, object]:
    context = enforce_roles(request=request, allowed_roles={"admin", "owner"}, workspace_fallback=payload.workspace_id)
    target_workspace = _resolve_target_workspace(context=context, requested_workspace_id=payload.workspace_id)
    quota = await upsert_workspace_quota(
        pool=get_pg_pool(),
        workspace_id=target_workspace,
        monthly_tx_quota=payload.monthly_tx_quota,
        is_active=payload.is_active,
    )
    return {"updated_by": context.subject_id, "quota": quota.to_dict()}


@router.get("/usage")
async def governance_usage(
    request: Request,
    workspace_id: str = Query(default="", max_length=64),
    months: int = Query(default=6, ge=1, le=24),
) -> dict[str, object]:
    context = enforce_roles(request=request, allowed_roles={"viewer", "operator", "admin", "owner"})
    target_workspace = _resolve_target_workspace(context=context, requested_workspace_id=workspace_id)
    rows = await list_workspace_usage(pool=get_pg_pool(), workspace_id=target_workspace, months=months)
    return {"workspace_id": target_workspace, "rows": rows}
