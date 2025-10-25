# backend/services/token_service.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import jwt  # PyJWT
from jwt import InvalidTokenError

from backend.config.settings import settings

# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _require_hs_secret():
    alg = (settings.jwt_algorithm or "HS256").upper()
    if not alg.startswith("HS"):
        # Para emitir tokens RS* se requeriría PRIVATE KEY (no tenemos en settings).
        raise NotImplementedError(
            f"Emisión de tokens requiere HS*; actual: {settings.jwt_algorithm}. "
            "Si necesitas RS*, agrega una PRIVATE KEY en settings y lo habilitamos."
        )
    if not settings.secret_key:
        raise ValueError("SECRET_KEY no configurada para HS*")

def _base_claims(exp_delta: timedelta, typ: str, extra: Dict[str, Any]) -> Dict[str, Any]:
    now = _now_utc()
    return {
        **extra,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + exp_delta).timestamp()),
        "typ": typ,
    }

# ─────────────────────────────────────────────────────────
# Create
# ─────────────────────────────────────────────────────────
def create_access_token(data: Dict[str, Any]) -> str:
    """Crea access token (HS*), expira en settings.access_token_expire_minutes."""
    _require_hs_secret()
    payload = _base_claims(
        timedelta(minutes=settings.access_token_expire_minutes),
        "access",
        data.copy(),
    )
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Crea refresh token (HS*), expira en 7 días."""
    _require_hs_secret()
    payload = _base_claims(timedelta(days=7), "refresh", data.copy())
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

# ─────────────────────────────────────────────────────────
# Decode (tipado)
# ─────────────────────────────────────────────────────────
def _decode_and_check_typ(token: str, expected_typ: str, allow_typeless: Optional[bool] = None) -> Optional[Dict[str, Any]]:
    """
    Decodifica y exige claim 'typ' == expected_typ.
    Si allow_typeless=True, acepta tokens sin 'typ' (compat).
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,  # Para HS*; (verificación RS* la hace jwt_service)
            algorithms=[settings.jwt_algorithm],
        )
        typ = payload.get("typ")
        if typ is None:
            if allow_typeless if allow_typeless is not None else settings.jwt_accept_typeless:
                return payload
            return None
        return payload if typ == expected_typ else None
    except InvalidTokenError:
        return None

def decode_access_token(token: str, *, allow_typeless: Optional[bool] = None) -> Optional[Dict[str, Any]]:
    return _decode_and_check_typ(token, "access", allow_typeless=allow_typeless)

def decode_refresh_token(token: str, *, allow_typeless: Optional[bool] = None) -> Optional[Dict[str, Any]]:
    return _decode_and_check_typ(token, "refresh", allow_typeless=allow_typeless)

# Alias legacy
def decode_token(token: str) -> Optional[Dict[str, Any]]:
    return decode_access_token(token)

# ─────────────────────────────────────────────────────────
# Reissue (refresh flow)
# ─────────────────────────────────────────────────────────
def reissue_tokens_from_refresh(
    refresh_token: str,
    *,
    allow_typeless: Optional[bool] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> Optional[Tuple[str, str]]:
    payload = decode_refresh_token(refresh_token, allow_typeless=allow_typeless)
    if not payload:
        return None
    reserved = {"exp", "iat", "nbf", "typ"}
    base = {k: v for k, v in payload.items() if k not in reserved}
    if extra_claims:
        base.update(extra_claims)
    return create_access_token(base), create_refresh_token(base)

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_access_token",
    "decode_refresh_token",
    "decode_token",
    "reissue_tokens_from_refresh",
]