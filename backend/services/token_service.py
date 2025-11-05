# backend/services/token_service.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import jwt  # PyJWT
from jwt import InvalidTokenError

from backend.config.settings import settings

# ─────────────────────────────────────────────────────────
# Utilidades internas (compatibles y no intrusivas)
# ─────────────────────────────────────────────────────────
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _effective_alg() -> str:
    """
    Algoritmo efectivo (normaliza a HS256 si viene en minúsculas o None).
    Mantiene compat total con tu configuración actual.
    """
    alg = (getattr(settings, "jwt_algorithm", None) or "HS256").upper()
    return alg

def _jwt_leeway_seconds() -> int:
    """
    Leeway de validación temporal para PyJWT (drift de reloj).
    Si tu settings define jwt_leeway_seconds o jwt_leeway, lo usamos; si no, 0.
    """
    for attr in ("jwt_leeway_seconds", "jwt_leeway"):
        try:
            v = int(getattr(settings, attr, 0) or 0)
            if v > 0:
                return v
        except Exception:
            pass
    return 0

def _access_exp_delta() -> timedelta:
    """
    Expiración del access token:
    usa settings.access_token_expire_minutes (por defecto 30 si no existe).
    """
    minutes = getattr(settings, "access_token_expire_minutes", None)
    try:
        m = int(minutes) if minutes is not None else 30
    except Exception:
        m = 30
    return timedelta(minutes=m)

def _refresh_exp_delta() -> timedelta:
    """
    Expiración del refresh:
    por defecto 7 días, pero si defines settings.refresh_token_expire_days, la respeta.
    """
    days = getattr(settings, "refresh_token_expire_days", None)
    try:
        d = int(days) if days is not None else 7
    except Exception:
        d = 7
    return timedelta(days=d)

def _require_hs_secret():
    """
    Asegura que estamos emitiendo con HS* y que hay SECRET_KEY.
    (No cambiamos tu política: si pides RS* aquí se mantiene el NotImplemented)
    """
    alg = _effective_alg()
    if not alg.startswith("HS"):
        raise NotImplementedError(
            f"Emisión de tokens requiere HS*; actual: {getattr(settings, 'jwt_algorithm', alg)}. "
            "Para RS*, agrega PRIVATE KEY y habilitamos."
        )
    if not getattr(settings, "secret_key", None):
        raise ValueError("SECRET_KEY no configurada para HS*")

def _base_claims(exp_delta: timedelta, typ: str, extra: Dict[str, Any]) -> Dict[str, Any]:
    now = _now_utc()
    # No tocamos tus claims; solo rellenamos los reservados
    return {
        **extra,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + exp_delta).timestamp()),
        "typ": typ,
    }

def _jwt_decode_kwargs() -> Dict[str, Any]:
    """
    Kwargs consistentes para jwt.decode (solo HS*).
    Respeta settings.jwt_accept_typeless (verificado en _decode_and_check_typ)
    y aplica leeway si está configurado.
    """
    leeway = _jwt_leeway_seconds()
    kwargs: Dict[str, Any] = {
        "algorithms": [_effective_alg()],
        # PyJWT valida exp/iat/nbf por defecto
        # Si en el futuro usas iss/aud, agrégalo aquí (issuer=..., audience=...)
    }
    if leeway > 0:
        kwargs["leeway"] = leeway
    return kwargs

# ─────────────────────────────────────────────────────────
# Create
# ─────────────────────────────────────────────────────────
def create_access_token(data: Dict[str, Any]) -> str:
    """Crea access token (HS*), expira en settings.access_token_expire_minutes (default 30)."""
    _require_hs_secret()
    payload = _base_claims(_access_exp_delta(), "access", data.copy())
    return jwt.encode(payload, settings.secret_key, algorithm=_effective_alg())

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Crea refresh token (HS*), expira en settings.refresh_token_expire_days (default 7)."""
    _require_hs_secret()
    payload = _base_claims(_refresh_exp_delta(), "refresh", data.copy())
    return jwt.encode(payload, settings.secret_key, algorithm=_effective_alg())

# ─────────────────────────────────────────────────────────
# Decode (tipado)
# ─────────────────────────────────────────────────────────
def _decode_and_check_typ(
    token: str,
    expected_typ: str,
    allow_typeless: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    """
    Decodifica y exige claim 'typ' == expected_typ.
    Si allow_typeless=True (o settings.jwt_accept_typeless), acepta tokens sin 'typ' (compat).
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,  # HS*
            **_jwt_decode_kwargs(),
        )
        typ = payload.get("typ")
        if typ is None:
            accept_typeless = (
                allow_typeless
                if allow_typeless is not None
                else bool(getattr(settings, "jwt_accept_typeless", False))
            )
            return payload if accept_typeless else None
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
    """
    A partir de un refresh válido, reemite (access, refresh).
    Mantiene tu firma y comportamiento: devuelve None si refresh inválido.
    """
    payload = decode_refresh_token(refresh_token, allow_typeless=allow_typeless)
    if not payload:
        return None

    # Quita claims reservados antes de reemitir
    reserved = {"exp", "iat", "nbf", "typ"}
    base = {k: v for k, v in payload.items() if k not in reserved}

    if extra_claims:
        base.update(extra_claims)

    return create_access_token(base), create_refresh_token(base)

# ─────────────────────────────────────────────────────────
# (Opcional) Helpers públicos pequeños, sin romper nada
# ─────────────────────────────────────────────────────────
def get_subject(payload: Dict[str, Any]) -> Optional[str]:
    """
    Extrae 'sub' o, en su defecto, 'user_id' o 'email' como identificador.
    No se usa internamente para no romper tu negocio; queda disponible por si lo necesitas.
    """
    return payload.get("sub") or payload.get("user_id") or payload.get("email")

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_access_token",
    "decode_refresh_token",
    "decode_token",
    "reissue_tokens_from_refresh",
    # helpers opcionales (no obligatorios)
    "get_subject",
]
