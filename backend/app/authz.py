from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, Request

from app.config import get_settings

_VALID_ROLES = {"viewer", "operator", "admin", "owner"}


@dataclass(frozen=True)
class AuthContext:
    subject_id: str
    workspace_id: str
    role: str
    auth_mode: str


def _normalize_role(role: str | None, default: str) -> str:
    candidate = (role or "").strip().lower()
    if candidate in _VALID_ROLES:
        return candidate
    return default


def resolve_auth_context(request: Request, workspace_fallback: str = "default") -> AuthContext:
    settings = get_settings()
    workspace_header = request.headers.get("x-workspace-id")
    workspace_id = (workspace_header or workspace_fallback or "default").strip() or "default"

    default_role = settings.default_workspace_role
    role_header = request.headers.get("x-workspace-role")
    role = _normalize_role(role_header, default_role)

    subject_id = (
        request.headers.get("x-auth-subject")
        or request.headers.get("x-forwarded-user")
        or request.headers.get("x-user-id")
        or "anonymous"
    ).strip() or "anonymous"

    return AuthContext(
        subject_id=subject_id,
        workspace_id=workspace_id,
        role=role,
        auth_mode=settings.auth_mode,
    )


def enforce_roles(request: Request, allowed_roles: set[str], workspace_fallback: str = "default") -> AuthContext:
    context = resolve_auth_context(request=request, workspace_fallback=workspace_fallback)
    settings = get_settings()
    if settings.auth_mode == "off":
        return context
    if context.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "insufficient_role",
                "required_any_of": sorted(allowed_roles),
                "actual_role": context.role,
                "workspace_id": context.workspace_id,
            },
        )
    return context
