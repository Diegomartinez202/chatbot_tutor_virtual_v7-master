# backend/routes/auth.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from backend.dependencies.auth import get_current_user
from backend.services.token_service import (
    create_access_token,
    create_refresh_token,
)
from backend.config.settings import settings
from backend.utils.logging import get_logger
from backend.rate_limit import limit
from backend.services.auth_service import (
    registrar_login_exitoso,
    registrar_acceso_perfil,
    login_user,
)
from backend.services.user_service import crear_usuario_si_no_existe

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ========================
# Modelos Pydantic
# ========================
class RegisterRequest(BaseModel):
    nombre: str
    email: EmailStr
    password: str


# ========================
# Helpers de cookie refresh
# ========================
def _refresh_cookie_name() -> str:
    return (settings.refresh_cookie_name or "rt").strip()

def _refresh_cookie_path() -> str:
    """
    Muy importante: como sirves el backend detrás de Nginx en /api,
    el path de la cookie debe ser /api/auth para que el navegador
    la envíe a /api/auth/refresh.
    """
    # Si algún día cambias el prefijo público, ajusta aquí
    return "/api/auth"

def _cookie_samesite() -> str:
    # En local sin https → Lax; en prod con https → None para permitir cross-site
    return "Lax" if (settings.debug or str(getattr(settings, "app_env", "dev")).lower() == "dev") else "None"

def _cookie_secure() -> bool:
    # Secure solo en https real (prod)
    return not settings.debug

def _set_refresh_cookie(response: JSONResponse, refresh_token: str) -> None:
    response.set_cookie(
        key=_refresh_cookie_name(),
        value=refresh_token,
        httponly=True,
        secure=_cookie_secure(),
        samesite=_cookie_samesite(),
        path=_refresh_cookie_path(),
        max_age=7 * 24 * 3600,
    )

def _clear_refresh_cookie(response: JSONResponse) -> None:
    response.delete_cookie(
        key=_refresh_cookie_name(),
        path=_refresh_cookie_path(),
    )


# ========================
# Login de usuario
# ========================
@router.post("/login")
@limit("10/minute")
def login_user_route(data: RegisterRequest, request: Request):
    """Login de usuario con email y password."""
    user = login_user(data.email, data.password)
    if not user:
        logger.warning(f"Login fallido: {data.email}")
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    registrar_login_exitoso(request, user)

    response = JSONResponse(
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,  # conservamos para compat
            "token_type": "bearer",
        }
    )
    _set_refresh_cookie(response, refresh_token)
    return response


# ========================
# Perfil autenticado
# ========================
@router.get("/me")
@limit("60/minute")
def get_profile(request: Request, current_user=Depends(get_current_user)):
    """Devuelve el perfil del usuario autenticado."""
    registrar_acceso_perfil(request, current_user)
    return {
        "email": current_user.get("email"),
        "nombre": current_user.get("nombre"),
        "rol": current_user.get("rol", "usuario"),
    }


# ========================
# Registro de usuario
# ========================
@router.post("/register")
@limit("5/minute")
def register_user(data: RegisterRequest, request: Request):
    """Crea un nuevo usuario y retorna tokens."""
    try:
        nuevo_usuario = crear_usuario_si_no_existe(
            nombre=data.nombre.strip(),
            email=data.email.lower(),
            password=data.password,
        )

        if not nuevo_usuario:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo ya esta registrado.",
            )

        logger.info(f"Usuario registrado: {data.email}")

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
        _set_refresh_cookie(response, refresh_token)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en registro: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error interno al registrar usuario: {str(e)}"
        )


# ========================
# Refresh de access token (cookie httpOnly)
# ========================
@router.post("/refresh")
@limit("30/minute")
def refresh_access_token(request: Request):
    """
    Lee la cookie httpOnly con el refresh y emite un nuevo access token.
    No devuelve un refresh nuevo (solo rotación de access).
    """
    # 1) Leer cookie
    cookie_name = _refresh_cookie_name()
    rt = request.cookies.get(cookie_name)
    if not rt:
        logger.info("Refresh sin cookie")
        raise HTTPException(status_code=401, detail="No refresh cookie")

    # 2) Decodificar/validar refresh y obtener el 'sub' (usuario)
    # Intentamos funciones típicas de tu token_service sin romper si no existen.
    user_payload = None
    user_id = None
    user_email = None

    try:
        # a) verify_refresh_token → {sub, ...}
        from backend.services import token_service as ts  # import perezoso

        if hasattr(ts, "verify_refresh_token"):
            user_payload = ts.verify_refresh_token(rt)
        elif hasattr(ts, "decode_refresh_token"):
            user_payload = ts.decode_refresh_token(rt)
        elif hasattr(ts, "get_subject_from_refresh"):
            user_payload = {"sub": ts.get_subject_from_refresh(rt)}  # puede ser id o email

        if user_payload:
            user_id = user_payload.get("sub") or user_payload.get("user_id")
            user_email = user_payload.get("email")
    except Exception as e:
        logger.warning(f"Refresh inválido: {e}")
        raise HTTPException(status_code=401, detail="Refresh inválido")

    if not (user_id or user_email):
        logger.warning("Refresh sin sub/email")
        raise HTTPException(status_code=401, detail="Refresh inválido")

    # 3) Recuperar usuario con los servicios disponibles
    user_obj = None
    try:
        # Preferimos buscar por id, y si no existe, por email.
        from backend.services import user_service as us  # import perezoso

        if user_id and hasattr(us, "get_user_by_id"):
            user_obj = us.get_user_by_id(user_id)
        if not user_obj and user_email:
            # nombres comunes
            for fn in ("find_user_by_email", "get_user_by_email", "buscar_usuario_por_email"):
                if hasattr(us, fn):
                    user_obj = getattr(us, fn)(user_email)
                    if user_obj:
                        break
    except Exception as e:
        logger.warning(f"No se pudo resolver usuario desde refresh: {e}")

    if not user_obj:
        logger.warning("Usuario no encontrado para refresh")
        raise HTTPException(status_code=401, detail="Refresh inválido")

    # 4) Emitimos nuevo access (no rotamos refresh aquí)
    try:
        new_access = create_access_token(user_obj)
    except Exception as e:
        logger.error(f"Error creando nuevo access desde refresh: {e}")
        raise HTTPException(status_code=500, detail="No fue posible rotar el access token")

    return {"access_token": new_access, "token_type": "bearer"}


# ========================
# Logout (borra refresh cookie)
# ========================
@router.post("/logout")
@limit("30/minute")
def logout_route():
    """Borra la cookie httpOnly de refresh para cerrar sesión en el navegador."""
    response = JSONResponse(content={"ok": True})
    _clear_refresh_cookie(response)
    return response
