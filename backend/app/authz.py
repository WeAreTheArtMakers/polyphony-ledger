from __future__ import annotations

import threading
from dataclasses import dataclass

import httpx
import jwt

from fastapi import HTTPException, Request

from app.config import get_settings

_VALID_ROLES = {"viewer", "operator", "admin", "owner"}
_ROLE_PRIORITY = {"viewer": 1, "operator": 2, "admin": 3, "owner": 4}
_OIDC_DISCOVERY_CACHE: dict[str, str] = {}
_OIDC_JWKS_CLIENTS: dict[str, jwt.PyJWKClient] = {}
_OIDC_LOCK = threading.Lock()


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


def _read_claim(claims: dict, path: str) -> object | None:
    current: object = claims
    for segment in (path or "").strip().split("."):
        if not segment:
            continue
        if not isinstance(current, dict):
            return None
        current = current.get(segment)
    return current


def _extract_role_candidates(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        tokens = [x.strip().lower() for x in value.replace(";", ",").split(",")]
        return [token for token in tokens if token]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, str):
                normalized = item.strip().lower()
                if normalized:
                    out.append(normalized)
        return out
    return []


def _pick_best_role(candidates: list[str], default_role: str) -> str:
    valid = [role for role in candidates if role in _VALID_ROLES]
    if not valid:
        return default_role
    valid.sort(key=lambda role: _ROLE_PRIORITY.get(role, 0), reverse=True)
    return valid[0]


def _parse_workspace_claim(value: object, fallback: str) -> str:
    if isinstance(value, str):
        normalized = value.strip()
        if normalized:
            return normalized
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                normalized = item.strip()
                if normalized:
                    return normalized
    return fallback


def _resolve_jwks_url(issuer_url: str) -> str:
    cached = _OIDC_DISCOVERY_CACHE.get(issuer_url)
    if cached:
        return cached

    discovery_url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
    response = httpx.get(discovery_url, timeout=5.0)
    response.raise_for_status()
    payload = response.json()
    jwks_uri = str(payload.get("jwks_uri", "")).strip()
    if not jwks_uri:
        raise RuntimeError(f"jwks_uri missing in OIDC discovery response for issuer={issuer_url}")
    _OIDC_DISCOVERY_CACHE[issuer_url] = jwks_uri
    return jwks_uri


def _get_oidc_jwks_client() -> jwt.PyJWKClient:
    settings = get_settings()
    issuer = settings.oidc_issuer_url.strip()
    if not issuer:
        raise RuntimeError("OIDC_ISSUER_URL must be set when AUTH_MODE=oidc")
    jwks_url = settings.oidc_jwks_url.strip() or _resolve_jwks_url(issuer)

    with _OIDC_LOCK:
        client = _OIDC_JWKS_CLIENTS.get(jwks_url)
        if client is None:
            client = jwt.PyJWKClient(jwks_url)
            _OIDC_JWKS_CLIENTS[jwks_url] = client
        return client


def _extract_bearer_token(request: Request) -> str:
    authorization = (request.headers.get("authorization") or "").strip()
    if not authorization:
        raise HTTPException(status_code=401, detail={"error": "missing_authorization_header"})
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail={"error": "invalid_authorization_scheme"})
    return token.strip()


def _resolve_oidc_context(request: Request, workspace_fallback: str) -> AuthContext:
    settings = get_settings()
    token = _extract_bearer_token(request)
    algorithms = [alg.strip() for alg in settings.oidc_algorithms.split(",") if alg.strip()]
    if not algorithms:
        algorithms = ["RS256"]

    try:
        jwks_client = _get_oidc_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=algorithms,
            audience=settings.oidc_audience or None,
            issuer=settings.oidc_issuer_url.strip() or None,
            options={
                "verify_aud": bool(settings.oidc_audience.strip()),
                "verify_iss": bool(settings.oidc_issuer_url.strip()),
            },
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail={"error": "token_expired"}) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail={"error": "invalid_token", "reason": str(exc)}) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"error": "oidc_unavailable", "reason": str(exc)}) from exc

    subject_claim = settings.oidc_subject_claim.strip() or "sub"
    subject_id = str(_read_claim(claims, subject_claim) or claims.get("sub") or "anonymous").strip() or "anonymous"

    role_sources = [
        settings.oidc_role_claim.strip(),
        "roles",
        "role",
        "realm_access.roles",
    ]
    role_candidates: list[str] = []
    for role_source in role_sources:
        role_candidates.extend(_extract_role_candidates(_read_claim(claims, role_source)))
    role = _pick_best_role(role_candidates, settings.default_workspace_role)

    workspace_source = settings.oidc_workspace_claim.strip() or "workspace_id"
    workspace_id = _parse_workspace_claim(
        _read_claim(claims, workspace_source),
        workspace_fallback.strip() or "default",
    )

    return AuthContext(
        subject_id=subject_id,
        workspace_id=workspace_id,
        role=role,
        auth_mode=settings.auth_mode,
    )


def resolve_auth_context(request: Request, workspace_fallback: str = "default") -> AuthContext:
    settings = get_settings()
    if settings.auth_mode == "oidc":
        return _resolve_oidc_context(request=request, workspace_fallback=workspace_fallback)

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
