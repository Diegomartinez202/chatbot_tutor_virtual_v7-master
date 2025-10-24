# backend/dependencies/auth.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# (Se mantiene la importación aunque hoy no se use directamente;
#  varios módulos previos esperan que esté disponible aquí)
from backend.db.mongodb import get_users_collection  # noqa: F401
from backend.config.settings import settings  # ✅ Config centralizada

# ============================
# 🔐 CONFIGURACIÓN JWT
# ============================

SECRET_KEY: str = settings.secret_key
ALGORITHM: str = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(getattr(settings, "access_token_expire_minutes", 60))

# Compat de documentación OAuth2 en /docs:
# En tus rutas actuales el login de usuario está en /auth/login,
# así que lo apuntamos allí (antes estaba /api/auth/login).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Opcionales (no obligamos; sólo si se configuran):
JWT_ISSUER: Optional[str] = getattr(settings, "jwt_issuer", None)
JWT_AUDIENCE: Optional[str] = getattr(settings, "jwt_audience", None)
JWT_LEEWAY_SECONDS: int = int(getattr(settings, "jwt_leeway_seconds", 0))
JWT_ACCEPT_TYPELESS: bool = bool(getattr(settings, "jwt_accept_typeless", True))  # compat con otros módulos


# ============================
# 🎟️ CREAR TOKEN
# ============================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un JWT de acceso (bearer). Mantiene compat con el resto del proyecto:
    - Usa SECRET_KEY / ALGORITHM de settings
    - Incluye 'exp' e 'iat'
    - Si hay issuer/audience configurados, los agrega
    """
    to_encode = dict(data or {})
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    claims: Dict = {
        **to_encode,
        "exp": expire,
        "iat": now,
    }
    if JWT_ISSUER:
        claims["iss"] = JWT_ISSUER
    if JWT_AUDIENCE:
        claims["aud"] = JWT_AUDIENCE

    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)


# ============================
# ❌ EXCEPCIÓN ESTÁNDAR
# ============================

def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ============================
# ✅ VERIFICAR TOKEN
# ============================

def _decode(token: str) -> Dict:
    """
    Decodifica el JWT aplicando la configuración disponible.
    - Verifica algoritmo/clave
    - Aplica leeway si se configuró
    - Si se definieron issuer/audience, también los verifica
    - Permite tokens sin 'typ' si JWT_ACCEPT_TYPELESS=True (compat)
    """
    decode_opts = {
        "verify_signature": True,
        "verify_aud": bool(JWT_AUDIENCE),
        "verify_iss": bool(JWT_ISSUER),
        # Aceptamos tokens sin 'typ' por compat si así se configuró
        "require_exp": True,
    }

    try:
        claims = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE if JWT_AUDIENCE else None,
            issuer=JWT_ISSUER if JWT_ISSUER else None,
            options=decode_opts,
            leeway=JWT_LEEWAY_SECONDS or 0,
        )
        # Compat: si se exige 'typ' en otros servicios y aquí no viene,
        # lo toleramos si JWT_ACCEPT_TYPELESS=True.
        if not JWT_ACCEPT_TYPELESS:
            typ = claims.get("typ")
            if typ not in (None, "access", "bearer", "JWT"):
                # Si tuvieras una política estricta de tipos, ajusta aquí.
                pass
        return claims
    except JWTError:
        raise credentials_exception()


def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Valida el token bearer y devuelve un payload normalizado que el resto
    de la app ya consume: {'id', 'email', 'rol'}.
    """
    claims = _decode(token)

    # Compat: en varios sitios se usa 'sub' como ID del usuario; lo normalizamos a 'id'
    user_id = claims.get("sub") or claims.get("id")
    email = claims.get("email")
    rol = claims.get("rol") or claims.get("role")

    if not user_id or not rol:
        # Mantiene el mismo mensaje/forma de error
        raise credentials_exception()

    return {"id": user_id, "email": email, "rol": rol}


# ============================
# 🛡️ CONTROL DE ROL
# ============================

def require_role(allowed_roles: List[str]):
    """
    Dependencia para FastAPI que valida que el usuario autenticado
    tenga un rol incluido en 'allowed_roles'. Reutilizada por tus routers.
    """
    def role_checker(user: dict = Depends(verify_token)):
        if user.get("rol") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para acceder a este recurso",
            )
        return user
    return role_checker


# ============================
# 🙋 USUARIO ACTUAL (sin validar rol)
# ============================

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Extrae y retorna los datos del usuario autenticado desde el token JWT.
    Mantiene compat con el retorno {'id', 'email', 'rol'} que el resto de
    la lógica ya espera.
    """
    return verify_token(token)