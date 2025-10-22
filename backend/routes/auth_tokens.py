from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.config.settings import settings
from backend.utils.logging import get_logger
from backend.dependencies.auth import get_current_user
from backend.utils.jwt_manager import (
    create_access_token,
    decode_token,
)
from backend.rate_limit import limit

# Auditoría / bitácora
from backend.services.auth_service import (
    registrar_logout,
    registrar_refresh_token,
)

# Lookup de usuario para refresh manual (body)
try:
    from backend.services.auth_service import find_user_by_email  # type: ignore
except Exception:
    try:
        from backend.services.user_service import find_user_by_email  # type: ignore
    except Exception:
        def find_user_by_email(_: str):
            return None  # fallback inocuo si no existe

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth Tokens"])


# ========================
# 🔒 LOGOUT (borra cookie refresh_token)
# ========================
@router.post("/logout")
@limit("30/minute")
def logout(request: Request, current_user=Depends(get_current_user)):
    """
    🔒 Cierra sesión del usuario autenticado.
    - Registra auditoría.
    - Elimina cookie httpOnly con refresh_token.
    """
    registrar_logout(request, current_user)
    logger.info(f"🚪 Logout: {current_user.get('email')}")

    resp = JSONResponse({"message": "Sesión cerrada correctamente"})
    resp.delete_cookie(settings.refresh_cookie_name)
    return resp


# ========================
# 🔁 REFRESH (usa cookie + get_current_user)
# ========================
@router.post("/refresh")
@limit("60/minute")
def refresh_access_token(request: Request, current_user=Depends(get_current_user)):
    """
    🔁 Genera un nuevo access token usando el refresh token enviado por cookie (vía get_current_user).
    - No devuelve ni toca el refresh token.
    - Registra el evento en auditoría.
    """
    access_token = create_access_token(current_user)
    registrar_refresh_token(request, current_user)
    logger.info(f"🔁 Access token renovado (cookie): {current_user.get('email')}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# ========================
# 🔁 REFRESH (por body) — alternativo
# ========================
class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh-token")
@limit("60/minute")
def refresh_access_token_manual(data: RefreshTokenRequest, request: Request):
    """
    🔁 Alternativa para renovar access token enviando el refresh_token en el body.
    - Útil para apps móviles o flujos sin cookies httpOnly.
    """
    try:
        payload = decode_token(
            data.refresh_token,
            secret=settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )
        email = payload.get("email")
        user_id = payload.get("id")
        if not email or not user_id:
            raise HTTPException(status_code=400, detail="Token inválido")

        user = find_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        access_token = create_access_token(user)
        registrar_refresh_token(request, user)
        logger.info(f"🔁 Access token renovado (body): {email}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en refresh-token (body): {str(e)}")
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")


# ========================
# 🔎 VERIFICAR / INTROSPECT (opcional)
# ========================
class VerifyTokenRequest(BaseModel):
    token: str


@router.post("/token/verify")
@limit("120/minute")
def verify_token(req: VerifyTokenRequest):
    """
    🔎 Verifica un JWT (access o refresh) y retorna su payload si es válido.
    - Útil para diagnóstico y pruebas.
    """
    try:
        payload = decode_token(
            req.token,
            secret=settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )
        return {"valid": True, "payload": payload}
    except Exception as e:
        logger.warning(f"Token inválido en /token/verify: {e}")
        return {"valid": False, "error": "Token inválido o expirado"}