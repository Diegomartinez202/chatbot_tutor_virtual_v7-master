# backend/routes/auth.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from backend.dependencies.auth import get_current_user
from backend.services.token_service import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,  # usamos si existe (no rompe si ya está)
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
from fastapi.security import OAuth2PasswordRequestForm
from backend.dependencies.auth import require_role

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ========================
# Modelos Pydantic
# ========================
class RegisterRequest(BaseModel):
    nombre: str
    email: EmailStr
    password: str

class AdminCreateUserRequest(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: str = "usuario"

# ========================
# Helpers de cookie refresh (mínimos, no invasivos)
# ========================
def _refresh_cookie_name() -> str:
    return (getattr(settings, "refresh_cookie_name", None) or "rt").strip()

def _refresh_cookie_path() -> str:
    """
    Importante: detrás de Nginx sirves el backend bajo /api,
    por lo que el path de la cookie debe ser /api/auth
    para que el navegador la envíe a /api/auth/refresh.
    """
    return "/"

def _cookie_samesite() -> str:
 
    app_env = str(getattr(settings, "app_env", "dev")).lower()
    is_dev = getattr(settings, "debug", False) or app_env == "dev"
    return "Lax" if is_dev else "None"

def _cookie_secure() -> bool:
    
    return not getattr(settings, "debug", False)

def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=_refresh_cookie_name(),
        value=refresh_token,
        httponly=True,
        secure=_cookie_secure(),
        samesite=_cookie_samesite(),
        path=_refresh_cookie_path(),
        max_age=7 * 24 * 3600,
    )

def _clear_refresh_cookie(response: Response) -> None:
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
            "refresh_token": refresh_token,  # compat
            "token_type": "bearer",
        }
    )
    _set_refresh_cookie(response, refresh_token)
    return response

# ========================
# Login estilo OAuth2 (para Swagger /oauth2/password)
# ========================
@router.post("/token")
@limit("10/minute")
def login_token_route(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),  # 👈 AQUÍ el cambio importante
):
    """
    Endpoint compatible con OAuth2PasswordBearer.
    Swagger y clientes OAuth2 mandan 'username' y 'password' como formulario
    (application/x-www-form-urlencoded). Usamos username como email.
    """
    email = form_data.username
    password = form_data.password

    user = login_user(email, password)
    if not user:
        logger.warning(f"Login OAuth2 fallido: {email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Credenciales invalidas")

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    from fastapi.responses import JSONResponse
    from .auth import _set_refresh_cookie  

    response = JSONResponse(
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,
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
                "refresh_token": refresh_token,  # compat añadido
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
# Soporta GET y POST para compat con el panel/interceptor
# ========================
@router.get("/refresh")
@router.post("/refresh")
@limit("30/minute")
def refresh_access_token(request: Request):
    """
    Lee la cookie httpOnly con el refresh y emite un nuevo access token.
    No rota el refresh (preserva tu lógica y compat).
    """
    cookie_name = _refresh_cookie_name()
    rt = request.cookies.get(cookie_name)

    if not rt:
        logger.info("Refresh sin cookie")
        raise HTTPException(status_code=401, detail="No refresh cookie")

    try:
        # Usamos decode_refresh_token si existe (en tu token_service)
        payload = None
        try:
            payload = decode_refresh_token(rt)  # puede retornar None si inválido
        except Exception:
            payload = None

        if not payload:
            # Fallback ultra-compat vía import perezoso de token_service (si cambió API)
            from backend.services import token_service as ts
            if hasattr(ts, "verify_refresh_token"):
                payload = ts.verify_refresh_token(rt)
            elif hasattr(ts, "get_subject_from_refresh"):
                payload = {"sub": ts.get_subject_from_refresh(rt)}

        if not payload:
            raise HTTPException(status_code=401, detail="Refresh inválido")

        # Extrae identidad base (id/email) sin alterar tu modelo
        user_id = payload.get("sub") or payload.get("user_id")
        user_email = payload.get("email")

        # Busca el usuario con tus servicios existentes (no invasivo)
        user_obj = None
        try:
            from backend.services import user_service as us
            if user_id and hasattr(us, "get_user_by_id"):
                user_obj = us.get_user_by_id(user_id)
            if not user_obj and user_email:
                for fn in ("find_user_by_email", "get_user_by_email", "buscar_usuario_por_email"):
                    if hasattr(us, fn):
                        user_obj = getattr(us, fn)(user_email)
                        if user_obj:
                            break
        except Exception:
            user_obj = None

        if not user_obj:
            raise HTTPException(status_code=401, detail="Refresh inválido")

        new_access = create_access_token(user_obj)
        return {"access_token": new_access, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en refresh: {e}")
        raise HTTPException(status_code=500, detail="No fue posible refrescar el token")


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

@router.post("/oauth2/token", summary="Login OAuth2 (form-data, Swagger)", include_in_schema=False)
def login_token_route(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
):
    """
    Endpoint compatible con OAuth2PasswordBearer.
    Swagger manda 'username' y 'password' como formulario.
    Aquí usamos username como email.
    """
    email = form_data.username
    password = form_data.password

    user = login_user(email, password)
    if not user:
        logger.warning(f"Login OAuth2 fallido: {email}")
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

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

  # misma lógica de cookie que usas en /auth/login
    cookie_name = settings.refresh_cookie_name or "rt"
    secure_cookie = False if (getattr(settings, "app_env", "dev") == "dev") else True
    response.set_cookie(
        key=cookie_name,
        value=refresh_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/api/auth",
    )

    return response

@router.post("/admin/create-user", summary="Crear usuario (solo admin)")
@limit("30/minute")
def admin_create_user(
    data: AdminCreateUserRequest,
    request: Request,
    current=Depends(require_role(["admin"])),  # 👈 SOLO admin puede usar esto
):
    """
    Permite a un admin crear usuarios con rol:
    - usuario
    - admin
    - soporte
    - estudiante (si quieres usarlo también para eso)
    """
    # Validar rol permitido
    if data.rol not in ("admin", "usuario", "soporte", "estudiante"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rol no permitido",
        )

    nuevo = crear_usuario_si_no_existe(
        nombre=data.nombre.strip(),
        email=data.email.lower(),
        password=data.password,
        rol=data.rol,
    )

    if not nuevo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya está registrado.",
        )

    logger.info(f"Usuario creado por admin: {data.email} con rol {data.rol}")
    return nuevo
class ZajunaLoginRequest(BaseModel):
    nombre: str
    email: EmailStr


@router.post("/zajuna-login", summary="Login/registro estudiante desde Zajuna")
@limit("60/minute")
def zajuna_login(data: ZajunaLoginRequest, request: Request):
    """
    Simula el login/registro de un estudiante que viene desde Zajuna.
    - Si no existe, lo crea con rol="estudiante".
    - Si ya existe, reutiliza el usuario.
    Devuelve access y refresh token igual que /auth/login.
    """
    from backend.services.user_service import get_user_by_email

    email_norm = data.email.lower().strip()
    user = get_user_by_email(email_norm)

    if not user:
        # Lo creamos como estudiante; la contraseña aquí no se usará para login local
        user = crear_usuario_si_no_existe(
            nombre=data.nombre.strip(),
            email=email_norm,
            password="!",
            rol="estudiante",
        )
        if not user:
            raise HTTPException(
                status_code=500,
                detail="No fue posible crear el estudiante.",
            )

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    registrar_login_exitoso(request, user)

    response = JSONResponse(
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "rol": "estudiante",
        }
    )
    _set_refresh_cookie(response, refresh_token)
    return response