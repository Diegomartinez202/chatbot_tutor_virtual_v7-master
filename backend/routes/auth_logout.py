# backend/routers/auth_logout.py
from fastapi import APIRouter, Response
from backend.config.settings import settings

router = APIRouter()

@router.post("/logout", summary="Cerrar sesi�n (borra cookie de refresh)")
async def logout(response: Response):
    """
    Limpia la cookie httpOnly del refresh token.
    No requiere autenticaci�n previa para ser idempotente.
    """
    cookie_name = getattr(settings, "refresh_cookie_name", "rt") or "rt"

    # Borra cookie (varias directivas para maximizar compatibilidad)
    response.delete_cookie(
        key=cookie_name,
        path="/",
        domain=None,         # si usas dominio, ponlo aqu�
    )
    # Algunos clientes respetan mejor un Set-Cookie expl�cito:
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

    return {"detail": "logged out"}