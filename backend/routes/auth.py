from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from backend.dependencies.auth import get_current_user
from backend.utils.jwt_manager import create_access_token, create_refresh_token
from backend.config.settings import settings
from backend.utils.logging import get_logger
from backend.rate_limit import limit
from backend.services.auth_service import (
    registrar_login_exitoso,
    registrar_acceso_perfil,
    login_user,
)
from backend.services.user_service import crear_usuario_si_no_existe
from backend.utils.security import hash_password

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ========================
# 🔐 MODELOS Pydantic
# ========================
class RegisterRequest(BaseModel):
    nombre: str
    email: EmailStr
    password: str


# ========================
# 🔐 LOGIN DE USUARIO
# ========================
@router.post("/login")
@limit("10/minute")
def login_user_route(data: RegisterRequest, request: Request):
    """🔐 Login de usuario"""
    user = login_user(data.email, data.password)
    if not user:
        logger.warning(f"❌ Login fallido: {data.email}")
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    registrar_login_exitoso(request, user)

    response = JSONResponse(
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    )
    response.set_cookie(
        key=(settings.refresh_cookie_name or "rt"),
        value=refresh_token,
        httponly=True,
        secure=not settings.debug,
        samesite="Lax",
        path="/",
        max_age=7 * 24 * 3600,
    )
    return response


# ========================
# 👤 PERFIL AUTENTICADO
# ========================
@router.get("/me")
@limit("60/minute")
def get_profile(request: Request, current_user=Depends(get_current_user)):
    """Devuelve perfil del usuario autenticado"""
    registrar_acceso_perfil(request, current_user)
    return {
        "email": current_user.get("email"),
        "nombre": current_user.get("nombre"),
        "rol": current_user.get("rol", "usuario"),
    }


# ========================
# 🆕 REGISTRO DE USUARIO
# ========================
@router.post("/register")
@limit("5/minute")
def register_user(data: RegisterRequest, request: Request):
    """🆕 Crea un nuevo usuario"""
    try:
        nuevo_usuario = crear_usuario_si_no_existe(
            nombre=data.nombre.strip(),
            email=data.email.lower(),
            password=data.password,
        )

        if not nuevo_usuario:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo ya está registrado.",
            )

        logger.info(f"👤 Usuario registrado: {data.email}")

        # Auto login tras registro
        access_token = create_access_token(nuevo_usuario)
        refresh_token = create_refresh_token(nuevo_usuario)

        response = JSONResponse(
            content={
                "message": "Cuenta creada exitosamente.",
                "access_token": access_token,
                "token_type": "bearer",
            },
            status_code=201,
        )

        response.set_cookie(
            key=(settings.refresh_cookie_name or "rt"),
            value=refresh_token,
            httponly=True,
            secure=not settings.debug,
            samesite="Lax",
            path="/",
            max_age=7 * 24 * 3600,
        )

        return response

    except Exception as e:
        logger.error(f"❌ Error en registro: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error interno al registrar usuario: {str(e)}"
        )