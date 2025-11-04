# backend/utils/jwt_manager.py
from __future__ import annotations

from typing import Any, Dict, Optional

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
    # Si mañana cambias el prefijo público, ajusta aquí de forma centralizada.
    return "/api/auth"


def refresh_cookie_samesite() -> str:
    """
    Política SameSite:
    - En local (debug o APP_ENV=dev): 'Lax' (permite flows normales sin https)
    - En producción con https real: 'None' (para permitir cross-site) + Secure=True
    """
    app_env = (getattr(settings, "app_env", None) or "").lower()
    if settings.debug or app_env == "dev":
        return "Lax"
    return "None"


def refresh_cookie_secure() -> bool:
    """
    Flag Secure:
    - Solo True en producción (https real). En local, False.
    """
    return not settings.debug


def set_refresh_cookie(response: JSONResponse, refresh_token: str) -> None:
    """
    Fija la cookie httpOnly de refresh en la respuesta, con parámetros correctos
    para tu reverse proxy (/api) y para desarrollo/producción.
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
# (útil en /auth/refresh si quieres centralizar la lógica)
# ─────────────────────────────────────────────────────────────
def try_reissue_access_from_request_cookie(
    request: Request,
) -> Dict[str, Any]:
    """
    Lee el refresh desde la cookie del request y reemite un access token nuevo.
    - Usa tu función `reissue_tokens_from_refresh` si existe (preferente).
    - Si no, intenta `decode_refresh_token` + `create_access_token`.
    Retorna: {"access_token": "..."} o lanza HTTPException(401/500).
    """
    cookie_key = refresh_cookie_name()
    rt = request.cookies.get(cookie_key)
    if not rt:
        raise HTTPException(status_code=401, detail="No refresh cookie")

    # Camino 1: si tienes una utilidad de reemisión completa, úsala (mantén tu negocio).
    try:
        # La firma típica devuelve dict con 'access_token' y opcional 'refresh_token'
        data = reissue_tokens_from_refresh(rt)  # type: ignore
        new_access = data.get("access_token")
        if not new_access:
            # Si no trajo access, probamos camino 2
            raise ValueError("No access_token in reissue payload")
        return {"access_token": new_access}
    except Exception:
        # Camino 2 (fallback): decodifica refresh → emite access
        try:
            payload = decode_refresh_token(rt)
            # sub puede ser id o email según tu implementación
            sub = payload.get("sub") or payload.get("user_id") or payload.get("email")
            if not sub:
                raise HTTPException(status_code=401, detail="Refresh inválido (sin sub)")
            # create_access_token acepta 'user' (objeto/dict) o un identificador según tu servicio
            new_access = create_access_token({"id": sub, "email": payload.get("email", None)})
            return {"access_token": new_access}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="Refresh inválido")
