from fastapi import APIRouter, Request, Response, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from backend.config.settings import settings
from backend.utils.jwt_manager import reissue_tokens_from_refresh

router = APIRouter()

class RefreshIn(BaseModel):
    refresh_token: Optional[str] = None  # opcional: puede venir por body o cookie

@router.post("/refresh", summary="Rotar tokens desde refresh token")
async def refresh_tokens(request: Request, response: Response, body: Optional[RefreshIn] = None):
    # 1) Tomar refresh token del body o de la cookie (compat con tu lógica actual)
    token = (body.refresh_token if body else None) or request.cookies.get(settings.refresh_cookie_name or "rt")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    # 2) Validar y reemitir
    pair = reissue_tokens_from_refresh(token, allow_typeless=settings.jwt_accept_typeless)
    if pair is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    access_token, new_refresh_token = pair

    # 3) Setear cookie httpOnly con el nuevo refresh (igual que tu flujo)
    cookie_name = settings.refresh_cookie_name or "rt"
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

    # 4) Devolver el access para el cliente (formato bearer)
    return {"access_token": access_token, "token_type": "bearer"}