# backend/routes/auth_routes_refactored.py
from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from backend.config.settings import settings
from backend.utils.jwt_manager import (
    create_access_token,
    create_refresh_token,
    decode_token,
    reissue_tokens_from_refresh,
)
from backend.logger import get_logger
from backend.services.auth_service import (
    registrar_login_exitoso,
    registrar_acceso_perfil,
    registrar_logout,
    registrar_refresh_token,
)
from backend.services.user_service import authenticate_user, find_user_by_email

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])

# ========================
# MODELOS Pydantic
# ========================
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# ========================
# LOGIN
# ========================
@router.post("/login", response_model=TokenResponse)
async def login(request_body: LoginRequest, request: Request, response: Response):
    user = authenticate_user(request_body.email, request_body.password)
    if not user:
        logger.warning(f"❌ Login fallido: {request_body.email}")
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    registrar_login_exitoso(request, user)
    logger.info(f"✅ Login exitoso: {user['email']}")

    # Cookie httpOnly para refresh token
    cookie_name = settings.refresh_cookie_name or "rt"
    secure_cookie = False if getattr(settings, "app_env", "dev") == "dev" else True
    response.set_cookie(
        key=cookie_name,
        value=refresh_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/",
    )

    return {"access_token": access_token, "token_type": "bearer"}

# ========================
# PERFIL ACTUAL
# ========================
def get_current_user(token: str = Depends()):
    """Extrae usuario desde access token"""
    try:
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Token inválido")
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

@router.get("/me")
async def me(request: Request, current_user: dict = Depends(get_current_user)):
    registrar_acceso_perfil(request, current_user)
    logger.info(f"📥 Acceso a perfil: {current_user['email']}")
    return {
        "email": current_user["email"],
        "nombre": current_user.get("nombre", ""),
        "rol": current_user.get("rol", "usuario"),
    }

# ========================
# LOGOUT
# ========================
@router.post("/logout")
async def logout(request: Request, response: Response, current_user: dict = Depends(get_current_user)):
    registrar_logout(request, current_user)
    logger.info(f"🚪 Logout: {current_user['email']}")

    cookie_name = settings.refresh_cookie_name or "rt"
    response.delete_cookie(cookie_name)
    return {"message": "Sesión cerrada correctamente"}

# ========================
# REFRESH (automático vía cookie)
# ========================
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(request: Request, response: Response):
    token = request.cookies.get(settings.refresh_cookie_name or "rt")
    if not token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    pair = reissue_tokens_from_refresh(token, allow_typeless=settings.jwt_accept_typeless)
    if not pair:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    access_token, new_refresh_token = pair

    cookie_name = settings.refresh_cookie_name or "rt"
    secure_cookie = False if getattr(settings, "app_env", "dev") == "dev" else True
    response.set_cookie(
        key=cookie_name,
        value=new_refresh_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/",
    )

    return {"access_token": access_token, "token_type": "bearer"}

# ========================
# REFRESH MANUAL (token en body)
# ========================
@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token_manual(body: RefreshTokenRequest, request: Request, response: Response):
    token = body.refresh_token
    if not token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    pair = reissue_tokens_from_refresh(token, allow_typeless=settings.jwt_accept_typeless)
    if not pair:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    access_token, new_refresh_token = pair

    cookie_name = settings.refresh_cookie_name or "rt"
    secure_cookie = False if getattr(settings, "app_env", "dev") == "dev" else True
    response.set_cookie(
        key=cookie_name,
        value=new_refresh_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/",
    )

    return {"access_token": access_token, "token_type": "bearer"}