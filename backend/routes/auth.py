# backend/routes/auth_routes.py

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.dependencies.auth import get_current_user
from backend.utils.jwt_manager import (
    create_access_token,
    create_refresh_token,
    decode_token,  # se mantiene por compatibilidad futura
)
from backend.config.settings import settings
from backend.utils.logging import get_logger

from backend.services.auth_service import (
    registrar_login_exitoso,
    registrar_acceso_perfil,
    registrar_logout,         # import legado (no usado aquí) — se mantiene para compatibilidad
    registrar_refresh_token,  # import legado (no usado aquí) — se mantiene para compatibilidad
)
from backend.models.auth_model import LoginRequest, TokenResponse
from backend.services.auth_service import login_user
from backend.rate_limit import limit

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

# ========================
# 🔐 Autenticación
# ========================

@router.post("/login", response_model=TokenResponse)
@limit("10/minute")  # frena intentos/brute force por IP/usuario
def login(request_body: LoginRequest, request: Request):
    """🔐 Login de usuario. Retorna access y refresh token."""
    # Ajuste: usar login_user (servicio oficial) en lugar de authenticate_user
    user = login_user(request_body.email, request_body.password)
    if not user:
        logger.warning(f"❌ Login fallido: {request_body.email}")
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    registrar_login_exitoso(request, user)
    logger.info(f"✅ Login exitoso para: {user.get('email', request_body.email)}")

    response = JSONResponse(
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    )

    # Cookie httpOnly para el refresh token (igual política que usas en tokens)
    response.set_cookie(
        key=(settings.refresh_cookie_name or "rt"),
        value=refresh_token,
        httponly=True,
        secure=not settings.debug,  # en dev permite no-secure
        samesite="Lax",
        path="/",
        max_age=7 * 24 * 3600,  # 7 días
    )

    return response


@router.get("/me")
@limit("60/minute")  # consultas de perfil
def get_profile(request: Request, current_user=Depends(get_current_user)):
    """👤 Devuelve perfil del usuario autenticado."""
    registrar_acceso_perfil(request, current_user)
    logger.info(f"📥 Acceso a perfil: {current_user.get('email')}")
    return {
        "email": current_user.get("email"),
        "nombre": current_user.get("nombre"),
        "rol": current_user.get("rol", "usuario"),
    }