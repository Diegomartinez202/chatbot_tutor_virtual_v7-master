# backend/utils/jwt_manager.py
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from backend.config.settings import settings
from backend.services.token_service import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    decode_token,
    reissue_tokens_from_refresh,
)

# ─────────────────────────────────────────────────────────────
# Re-exports (compatibilidad total con tu código actual)
# ─────────────────────────────────────────────────────────────
__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_access_token",
    "decode_refresh_token",
    "decode_token",
    "reissue_tokens_from_refresh",
    # Helpers nuevos (opcionales y no intrusivos):
    "refresh_cookie_name",
    "refresh_cookie_path",
    "refresh_cookie_samesite",
    "refresh_cookie_secure",
    "set_refresh_cookie",
    "clear_refresh_cookie",
    "try_reissue_access_from_request_cookie",
]

# ─────────────────────────────────────────────────────────────
# Helpers para cookie httpOnly de refresh (NO rompen nada)
# ─────────────────────────────────────────────────────────────
def refresh_cookie_name() -> str:
    """Nombre efectivo de la cookie de refresh (por defecto 'rt')."""
    return (getattr(settings, "refresh_cookie_name", None) or "rt").strip()


def refresh_cookie_path() -> str:
    """
    Path efectivo de la cookie de refresh.
    Como expones el backend detrás de Nginx bajo /api, aquí devolvemos '/api/auth'
    para que el navegador SÍ envíe la cookie a /api/auth/refresh.
    """
    return "/api/auth"


def refresh_cookie_samesite() -> str:
    """
    Política SameSite:
    - En local (debug o APP_ENV=dev): 'Lax'
    - En producción con https real: 'None' (requiere Secure=True)
    """
    app_env = (getattr(settings, "app_env", "") or "").lower()
    if settings.debug or app_env == "dev":
        return "Lax"
    return "None"


def refresh_cookie_secure() -> bool:
    """
    Flag Secure:
    - True solo en producción (https real). En local, False.
    """
    return not settings.debug


def set_refresh_cookie(response: JSONResponse, refresh_token: str) -> None:
    """
    Fija la cookie httpOnly de refresh con parámetros correctos.
    """
    response.set_cookie(
        key=refresh_cookie_name(),
        value=refresh_token,
        httponly=True,
        secure=refresh_cookie_secure(),
        samesite=refresh_cookie_samesite(),
        path=refresh_cookie_path(),
        max_age=7 * 24 * 3600,  # 7 días
    )


def clear_refresh_cookie(response: JSONResponse) -> None:
    """
    Elimina la cookie httpOnly de refresh (logout).
    """
    response.delete_cookie(
        key=refresh_cookie_name(),
        path=refresh_cookie_path(),
    )

# ─────────────────────────────────────────────────────────────
# Helper opcional: reemitir access leyendo refresh de la cookie
# Compatible con:
#  - token_service.reissue_tokens_from_refresh → Tuple[str, str]
#  - o dict {"access_token": "...", "refresh_token": "..."}
#  - o fallback con decode_refresh_token + create_access_token
# ─────────────────────────────────────────────────────────────
def try_reissue_access_from_request_cookie(request: Request) -> Dict[str, Any]:
    """
    Lee el refresh desde la cookie del request y reemite un access token nuevo.

    Retorna: {"access_token": "..."} o lanza HTTPException(401/500).
    """
    cookie_key = refresh_cookie_name()
    rt = request.cookies.get(cookie_key)
    if not rt:
        raise HTTPException(status_code=401, detail="No refresh cookie")

    # Camino 1: usar reissue_tokens_from_refresh si está disponible (tu servicio)
    try:
        result = reissue_tokens_from_refresh(rt)  # puede ser Tuple[str,str] o dict
        if result:
            # a) Tu implementación actual: Optional[Tuple[str, str]] (access, refresh)
            if isinstance(result, tuple) and len(result) == 2:
                new_access, _maybe_new_refresh = result  # no rotamos cookie aquí
                if not new_access:
                    raise ValueError("Tuple sin access token")
                return {"access_token": new_access}

            # b) Alternativa: dict {"access_token": "...", "refresh_token": "..."}
            if isinstance(result, dict):
                new_access = result.get("access_token")
                if new_access:
                    return {"access_token": new_access}
                # Si no trae access en el dict, cae a fallback
    except Exception:
        # Continuamos al fallback silenciosamente
        pass

    # Camino 2 (fallback): decodificar refresh y emitir access
    payload = None
    try:
        payload = decode_refresh_token(rt)
    except Exception:
        payload = None

    if not payload:
        raise HTTPException(status_code=401, detail="Refresh inválido")

    # sub puede ser id o email según tu implementación
    sub = payload.get("sub") or payload.get("user_id") or payload.get("id") or payload.get("email")
    if not sub:
        raise HTTPException(status_code=401, detail="Refresh inválido (sin sub)")

    # ⚠️ No asumimos estructura completa del usuario para no romper negocio.
    # Emitimos access con lo mínimo que usan tus dependencias: id/email/rol (si viene).
    base_claims: Dict[str, Any] = {"id": sub}
    if "email" in payload and payload.get("email"):
        base_claims["email"] = payload["email"]
    if "rol" in payload and payload.get("rol"):
        base_claims["rol"] = payload["rol"]

    try:
        new_access = create_access_token(base_claims)
        return {"access_token": new_access}
    except Exception:
        raise HTTPException(status_code=500, detail="No fue posible emitir nuevo access")
