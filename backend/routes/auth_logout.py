# backend/routers/auth_logout.py
from fastapi import APIRouter, Response
from backend.config.settings import settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.post("/logout", summary="Cerrar sesión (borra cookie de refresh)")
async def logout(response: Response):
    """
    Limpia la cookie httpOnly del refresh token.
    No requiere autenticación previa para ser idempotente.
    """
    cookie_name = getattr(settings, "refresh_cookie_name", "rt") or "rt"

    # Borra cookie (varias directivas para maximizar compatibilidad)
    response.delete_cookie(
        key=cookie_name,
        path="/",
        domain=None,         # si usas dominio, ponlo aquí
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