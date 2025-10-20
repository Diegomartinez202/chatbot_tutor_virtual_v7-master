# backend/routers/auth_token.py
from fastapi import APIRouter, Response, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional, Any, Dict

from backend.config.settings import settings
from backend.utils.jwt_manager import (
    create_access_token,
    create_refresh_token,
)

router = APIRouter()

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
