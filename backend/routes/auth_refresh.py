# backend/routers/auth_refresh.py
from fastapi import APIRouter, Request, Response, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from backend.config.settings import settings
from backend.utils.jwt_manager import reissue_tokens_from_refresh
from backend.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

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
    token = (body.refresh_token if body else None) or request.cookies.get(settings.refresh_cookie_name or "rt")
    if not token:
        logger.warning("Intento de refresh sin token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    # 2) Validar y reemitir
    pair = reissue_tokens_from_refresh(token, allow_typeless=settings.jwt_accept_typeless)
    if pair is None:
        logger.warning("Refresh token inválido o expirado")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    access_token, new_refresh_token = pair

    # 3) Setear cookie httpOnly con el nuevo refresh token
    cookie_name = settings.refresh_cookie_name or "rt"
    secure_cookie = False if getattr(settings, "app_env", "dev") == "dev" else True

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