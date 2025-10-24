# backend/routes/auth_tokens.py
from __future__ import annotations

from typing import Optional, Any, Dict

from fastapi import APIRouter, Request, Response, HTTPException, status
from pydantic import BaseModel, EmailStr

from backend.config.settings import settings
from backend.utils.logging import get_logger
from backend.utils.jwt_manager import (
    reissue_tokens_from_refresh,
    create_access_token,
    create_refresh_token,
)

logger = get_logger(__name__)

# Prefijo para agrupar con /auth
router = APIRouter(prefix="/auth", tags=["Auth Tokens"])


# ─────────────────────────────────────────────────────────────
# 🔁 REFRESH (cookie o body)
# ─────────────────────────────────────────────────────────────
class RefreshIn(BaseModel):
    refresh_token: Optional[str] = None  # opcional: puede venir por body o cookie


@router.post("/refresh", summary="Rotar tokens desde refresh token")
async def refresh_tokens(request: Request, response: Response, body: Optional[RefreshIn] = None):
    """
    Rotación de tokens usando refresh token:
    - Se acepta en body JSON o en cookie httpOnly
    - Devuelve nuevo access token y renueva la cookie refresh
    """
    cookie_name = (settings.refresh_cookie_name or "rt")
    token = (body.refresh_token if body else None) or request.cookies.get(cookie_name)
    if not token:
        logger.warning("Intento de refresh sin token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    pair = reissue_tokens_from_refresh(token, allow_typeless=getattr(settings, "jwt_accept_typeless", False))
    if pair is None:
        logger.warning("Refresh token inválido o expirado")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    access_token, new_refresh_token = pair

    secure_cookie = False if (getattr(settings, "app_env", "dev") == "dev") else True
    response.set_cookie(
        key=cookie_name,
        value=new_refresh_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=7 * 24 * 3600,  # 7 días
        path="/",
    )

    logger.info(f"🔁 Refresh token exitoso, nueva cookie establecida para '{cookie_name}'")
    return {"access_token": access_token, "token_type": "bearer"}


# ─────────────────────────────────────────────────────────────
# 🚪 LOGOUT (borra cookie de refresh)
# ─────────────────────────────────────────────────────────────
@router.post("/logout", summary="Cerrar sesión (borra cookie de refresh)")
async def logout(response: Response):
    """
    Limpia la cookie httpOnly del refresh token.
    No requiere autenticación previa para ser idempotente.
    """
    cookie_name = (getattr(settings, "refresh_cookie_name", "rt") or "rt")

    # Borrar cookie
    response.delete_cookie(
        key=cookie_name,
        path="/",
        domain=None,
    )
    # Set explícito para maximizar compatibilidad
    response.set_cookie(
        key=cookie_name,
        value="",
        max_age=0,
        expires=0,
        httponly=True,
        secure=False if getattr(settings, "app_env", "dev") == "dev" else True,
        samesite="lax",
        path="/",
    )

    logger.info(f"🚪 Logout ejecutado, cookie '{cookie_name}' eliminada")
    return {"detail": "logged out"}


# ─────────────────────────────────────────────────────────────
# 🔑 TOKEN (emitir access/refresh al hacer login)
# ─────────────────────────────────────────────────────────────
class TokenRequest(BaseModel):
    email: EmailStr
    password: str


def _try_builtin_verify(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Intenta delegar en tu lógica existente de autenticación.
    Preferimos backend.services.user_service.verify_user_credentials.
    Si no está, probamos backend.services.auth_service.verify_user_credentials.
    Debe devolver un dict usuario o None.
    """
    # 1) user_service
    try:
        from backend.services.user_service import verify_user_credentials  # type: ignore
        user = verify_user_credentials(email, password)
        if user:
            if not isinstance(user, dict):
                user = {
                    "id": getattr(user, "id", getattr(user, "_id", str(user))),
                    "email": getattr(user, "email", email),
                    "role": getattr(user, "role", "user"),
                }
            return user
    except Exception:
        pass

    # 2) auth_service (fallback)
    try:
        from backend.services.auth_service import verify_user_credentials  # type: ignore
        user = verify_user_credentials(email, password)  # type: ignore
        if user:
            if not isinstance(user, dict):
                user = {
                    "id": getattr(user, "id", getattr(user, "_id", str(user))),
                    "email": getattr(user, "email", email),
                    "role": getattr(user, "role", "user"),
                }
            return user
    except Exception:
        pass

    return None


def _try_bootstrap_admin(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Modo bootstrap **opcional**: solo permite login del admin si defines
    ADMIN_BOOTSTRAP_PASSWORD en el .env. No sustituye tu lógica.
    """
    if not settings.admin_bootstrap_password:
        return None
    if email.lower() == (settings.admin_email or "").lower() and password == settings.admin_bootstrap_password:
        return {
            "id": "admin-bootstrap",
            "email": email,
            "role": "admin",
        }
    return None


@router.post("/token", summary="Emitir access/refresh tokens (login)")
async def issue_tokens(payload: TokenRequest, response: Response):
    """
    Endpoint de emisión de tokens:
    1) Intenta verificar con la lógica existente (user_service/auth_service)
    2) Si no, permite bootstrap admin si ADMIN_BOOTSTRAP_PASSWORD está configurado
    3) Devuelve access como bearer y setea refresh en cookie httpOnly
    """
    # 1) Verificación propia
    user = _try_builtin_verify(payload.email, payload.password)

    # 2) Bootstrap admin (si configurado)
    if user is None:
        user = _try_bootstrap_admin(payload.email, payload.password)

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    base_claims = {
        "sub": str(user.get("id", user.get("_id", user.get("email")))),
        "email": user.get("email", payload.email),
        "role": user.get("role", "user"),
    }

    access_token = create_access_token({**base_claims, "typ": "access"})
    refresh_token = create_refresh_token({**base_claims, "typ": "refresh"})

    cookie_name = settings.refresh_cookie_name or "rt"
    secure_cookie = False if (getattr(settings, "app_env", "dev") == "dev") else True
    response.set_cookie(
        key=cookie_name,
        value=refresh_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/",
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": base_claims["sub"],
            "email": base_claims["email"],
            "role": base_claims["role"],
        },
    }