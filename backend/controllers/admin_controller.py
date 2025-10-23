# =====================================================
# 🧩 backend/controllers/admin_controller.py
# =====================================================
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional, Dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr

# Modelo de salida ya usado en tu proyecto
from backend.schemas.user_schema import UserOut

# Servicios reales (síncronos)
from backend.services.user_service import (
    create_user,
    get_user_by_email,
    verify_user_credentials,
)

# Settings (clave JWT, etc.)
from backend.config.settings import settings

# =====================================================
# JWT helpers (preferir tus dependencias si existen)
# =====================================================
_have_dep_auth = False
try:
    # Si existen, se usarán directamente
    from backend.dependencies.auth import create_access_token as dep_create_token  # type: ignore
    from backend.dependencies.auth import verify_token as dep_verify_token        # type: ignore
    _have_dep_auth = True
except Exception:
    _have_dep_auth = False

# Fallback a jwt_service si existe
_create_jwt = None
try:
    from backend.services.jwt_service import create_access_token as _create_jwt  # type: ignore
except Exception:
    _create_jwt = None  # type: ignore

# Fallback final: PyJWT
_pyjwt = None
try:
    import jwt as _pyjwt  # PyJWT
except Exception:
    _pyjwt = None  # type: ignore

JWT_ALG = "HS256"


def _local_create_access_token(claims: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Genera JWT con prioridad:
      1) backend.dependencies.auth.create_access_token (si está)
      2) backend.services.jwt_service.create_access_token (si está)
      3) PyJWT local (HS256)
    """
    if _have_dep_auth:
        return dep_create_token(claims, expires_delta)  # type: ignore[arg-type]

    if _create_jwt:
        return _create_jwt(claims)

    if _pyjwt is None:
        raise RuntimeError(
            "No hay implementaciones JWT disponibles. Instala pyjwt o agrega jwt_service "
            "o usa backend.dependencies.auth."
        )

    to_encode = dict(claims)
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(hours=8))
    to_encode.update({"iat": now, "exp": expire})
    return _pyjwt.encode(to_encode, settings.secret_key, algorithm=JWT_ALG)


def _local_decode_token(token: str) -> Dict:
    """
    Decodifica JWT con prioridad:
      1) backend.dependencies.auth.verify_token (si está)
      2) PyJWT local (HS256)
      3) backend.services.jwt_service.decode_token (si existe)
    """
    if _have_dep_auth:
        # verify_token ya valida y devuelve claims normalizados
        return dep_verify_token(token)  # type: ignore[arg-type]

    if _pyjwt is not None:
        try:
            return _pyjwt.decode(token, settings.secret_key, algorithms=[JWT_ALG])
        except Exception:
            raise HTTPException(status_code=401, detail="Token inválido o expirado.")

    try:
        from backend.services.jwt_service import decode_token as _decode  # type: ignore
        return _decode(token)
    except Exception:
        raise HTTPException(status_code=500, detail="No hay forma de decodificar el token.")


def _get_bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta token Bearer.")
    return auth.split(" ", 1)[1].strip()


# =====================================================
# 📦 Modelos
# =====================================================
class AdminRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    key: Optional[str] = None


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


router = APIRouter(prefix="/api/admin", tags=["Admin"])


# =====================================================
# 🧠 Registro de Administrador
# =====================================================
@router.post("/register", response_model=UserOut)
def register_admin(data: AdminRegister):
    # 1) Clave de registro opcional
    expected_key = os.getenv("ADMIN_REGISTER_KEY")
    if expected_key and data.key != expected_key:
        raise HTTPException(status_code=401, detail="Clave de registro incorrecta o ausente.")

    # 2) Duplicados
    existing = get_user_by_email(data.email)
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese correo.")

    # 3) Regla mínima de password
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres.")

    # 4) Crear usuario (el servicio ya hashea la contraseña)
    nuevo = create_user(nombre=data.name, email=data.email, password=data.password, rol="admin")
    if not nuevo:
        raise HTTPException(status_code=500, detail="Error creando el administrador.")

    # Mapear a salida (UserOut acepta id, nombre, email, rol)
    return {
        "id": str(nuevo.get("_id") or nuevo.get("id", "")),
        "nombre": nuevo.get("nombre", data.name),
        "email": nuevo.get("email", data.email),
        "rol": nuevo.get("rol", "admin"),
    }


# =====================================================
# 🔐 Login de Administrador
# =====================================================
@router.post("/login")
def login_admin(data: AdminLogin):
    user = verify_user_credentials(data.email, data.password)
    if not user or user.get("rol") != "admin":
        raise HTTPException(status_code=401, detail="Credenciales inválidas o no es administrador.")

    claims: Dict[str, str] = {
        "sub": user["email"],
        "email": user["email"],
        "rol": user["rol"],
    }
    token = _local_create_access_token(claims)
    return {"access_token": token, "token_type": "bearer"}


# =====================================================
# 🙋 Perfil del Administrador
# =====================================================
@router.get("/me", response_model=UserOut)
def get_admin_me(request: Request):
    token = _get_bearer_token(request)
    claims = _local_decode_token(token)

    email = claims.get("sub") or claims.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Token sin 'sub' o 'email'.")

    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if user.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="No autorizado para el panel administrativo.")

    return {
        "id": str(user.get("_id") or user.get("id", "")),
        "nombre": user.get("nombre", ""),
        "email": user.get("email", ""),
        "rol": user.get("rol", ""),
    }