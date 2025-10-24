# backend/routes/auth_tokens.py

from typing import Optional, Any, Dict

from fastapi import APIRouter, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from backend.config.settings import settings
from backend.utils.logging import get_logger
from backend.utils.jwt_manager import (
    reissue_tokens_from_refresh,
    create_access_token,
    create_refresh_token,
)

logger = get_logger(__name__)

# Dejamos el prefijo aquí para que en main.py no tengas que repetirlo
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
    # 1) Tomar refresh token del body o de la cookie
    cookie_name = (settings.refresh_cookie_name or "rt")
    token = (body.refresh_token if body else None) or request.cookies.get(cookie_name)
    if not token:
        logger.warning("Intento de refresh sin token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    # 2) Validar y reemitir
    pair = reissue_tokens_from_refresh(token, allow_typeless=getattr(settings, "jwt_accept_typeless", False))
    if pair is None:
        logger.warning("Refresh token inválido o expirado")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    access_token, new_refresh_token = pair

    # 3) Setear cookie httpOnly con el nuevo refresh token
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

    # 4) Devolver nuevo access token
    return {"access_token": access_token, "token_type": "bearer"}


# ─────────────────────────────────────────────────────────────
# 🔒 LOGOUT (borra cookie de refresh)
# ─────────────────────────────────────────────────────────────
@router.post("/logout", summary="Cerrar sesión (borra cookie de refresh)")
async def logout(response: Response):
    """
    Limpia la cookie httpOnly del refresh token.
    No requiere autenticación previa para ser idempotente.
    """
    cookie_name = (getattr(settings, "refresh_cookie_name", "rt") or "rt")

    # Borra cookie (varias directivas para maximizar compatibilidad)
    response.delete_cookie(
        key=cookie_name,
        path="/",
        domain=None,  # si usas dominio específico, colócalo aquí
    )

    # Algunos clientes respetan mejor un Set-Cookie explícito
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
    Intenta delegar en tu lógica existente de autenticación si está disponible.
    Debe devolver un dict con al menos: {"id": ..., "email": ..., "role": ...}
    Devuelve None si no puede verificar o si no existe esa función.
    """
    try:
        # Si tienes un servicio de auth propio, ajústalo aquí:
        from backend.services.auth_service import verify_user_credentials  # type: ignore
        # Debe devolver: None si no válido, o un usuario (dict/objeto con id/email/role)
        user = verify_user_credentials(email, password)
        if user:
            # Normalizamos a dict
            if not isinstance(user, dict):
                user = {
                    "id": getattr(user, "id", getattr(user, "_id", str(user))),
                    "email": getattr(user, "email", email),
                    "role": getattr(user, "role", "user"),
                }
            return user
    except Exception:
        # Si el módulo/función no existe o falla, seguimos con bootstrap opcional
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
    1) Intenta verificar con tu auth_service (verify_user_credentials)
    2) Si no, permite bootstrap admin si ADMIN_BOOTSTRAP_PASSWORD está configurado
    3) Devuelve access como bearer y setea refresh en cookie httpOnly
    """
    # 1) Primero intenta tu verificación propia
    user = _try_builtin_verify(payload.email, payload.password)

    # 2) Si no está disponible o es inválido, intenta bootstrap admin (si configurado)
    if user is None:
        user = _try_bootstrap_admin(payload.email, payload.password)

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # 3) Claims mínimos (agregamos 'typ' = 'access'/'refresh')
    base_claims = {
        "sub": str(user.get("id", user.get("_id", user.get("email")))),
        "email": user.get("email", payload.email),
        "role": user.get("role", "user"),
    }

    access_token = create_access_token({**base_claims, "typ": "access"})
    refresh_token = create_refresh_token({**base_claims, "typ": "refresh"})

    # 4) Cookie httpOnly para refresh (igual flujo que ya usamos)
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

    # 5) Devolvemos access como bearer (sin romper front)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": base_claims["sub"],
            "email": base_claims["email"],
            "role": base_claims["role"],
        },
    }
