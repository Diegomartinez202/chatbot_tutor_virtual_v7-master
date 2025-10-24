# backend/utils/jwt_manager.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
import os

from jose import jwt, JWTError
from backend.config.settings import settings  # ✅ Ya actualizado


def _bool_env(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def _accept_typeless_default() -> bool:
    """
    Lee el flag de compatibilidad:
    - settings.jwt_accept_typeless (si existe) o
    - env JWT_ACCEPT_TYPELESS (true/false)
    """
    accept_from_settings = getattr(settings, "jwt_accept_typeless", None)
    if isinstance(accept_from_settings, bool):
        return accept_from_settings
    return _bool_env("JWT_ACCEPT_TYPELESS", False)


def _base_claims(expire_delta: timedelta, typ: str, extra: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.utcnow()
    claims: Dict[str, Any] = {**extra}
    claims.update(
        {
            "exp": now + expire_delta,
            "iat": now,
            "typ": typ,  # separa access vs refresh
        }
    )
    return claims


def create_access_token(data: Dict[str, Any]) -> str:
    """
    Access token (corto): expira en minutos.
    Incluye typ="access".
    """
    to_encode = _base_claims(
        expire_delta=timedelta(minutes=settings.access_token_expire_minutes),  # ✅ actualizado
        typ="access",
        extra=data.copy(),
    )
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)  # ✅ actualizado


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Refresh token (largo): expira en 7 días.
    Incluye typ="refresh".
    """
    to_encode = _base_claims(
        expire_delta=timedelta(days=7),
        typ="refresh",
        extra=data.copy(),
    )
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)  # ✅ actualizado


def _decode_and_verify(token: str, expected_typ: str, *, allow_typeless: Optional[bool] = None) -> Optional[Dict[str, Any]]:
    """
    Decodifica y verifica que el claim 'typ' coincida con lo esperado.
    - Si allow_typeless=True y el token NO trae 'typ', lo acepta (compat temporal).
    Devuelve el payload si es válido; None en caso contrario.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])  # ✅ actualizado
        typ = payload.get("typ")

        if allow_typeless is None:
            allow_typeless = _accept_typeless_default()

        if typ is None:
            if allow_typeless:
                return payload
            return None

        if typ != expected_typ:
            return None

        return payload
    except JWTError:
        return None


def decode_access_token(token: str, *, allow_typeless: Optional[bool] = None) -> Optional[Dict[str, Any]]:
    """Valida un access token (typ='access')."""
    return _decode_and_verify(token, expected_typ="access", allow_typeless=allow_typeless)


def decode_refresh_token(token: str, *, allow_typeless: Optional[bool] = None) -> Optional[Dict[str, Any]]:
    """Valida un refresh token (typ='refresh')."""
    return _decode_and_verify(token, expected_typ="refresh", allow_typeless=allow_typeless)


# 🔹 Compatibilidad con tu middleware actual:
def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Alias para access token (no rompe imports existentes)."""
    return decode_access_token(token)


def reissue_tokens_from_refresh(
    refresh_token: str,
    *,
    allow_typeless: Optional[bool] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> Optional[Tuple[str, str]]:
    """
    Valida un refresh token y reemite (access, refresh) preservando claims relevantes.
    """
    payload = decode_refresh_token(refresh_token, allow_typeless=allow_typeless)
    if not payload:
        return None

    reserved = {"exp", "iat", "typ"}
    base_claims = {k: v for k, v in payload.items() if k not in reserved}

    if extra_claims:
        base_claims.update(extra_claims)

    new_access = create_access_token(base_claims)
    new_refresh = create_refresh_token(base_claims)
    return new_access, new_refresh


__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_access_token",
    "decode_refresh_token",
    "decode_token",
    "reissue_tokens_from_refresh",
]
