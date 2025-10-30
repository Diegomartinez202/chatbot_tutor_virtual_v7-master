# backend/dependencies/auth.py
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Usamos python-jose, manteniendo compat con tu import original
# (seguiremos usando 'jwt.encode' y 'jwt.decode' vía jose)
from jose import JWTError, jwt as jose_jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError as JoseCoreJWTError

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

# Extras para RS* (si los defines en .env/settings, se usan; si no, no molestan)
JWT_JWKS_URL: Optional[str] = getattr(settings, "jwt_jwks_url", os.getenv("JWT_JWKS_URL", None))
JWT_PUBLIC_KEY: Optional[str] = getattr(settings, "jwt_public_key", os.getenv("JWT_PUBLIC_KEY", None))


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

    claims: Dict[str, Any] = {
        **to_encode,
        "exp": expire,
        "iat": now,
    }
    if JWT_ISSUER:
        claims["iss"] = JWT_ISSUER
    if JWT_AUDIENCE:
        claims["aud"] = JWT_AUDIENCE

    # Mantiene tu interfaz (jwt.encode)
    return jose_jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)


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

def _resolve_key_for_decode(token: str, algorithm: str) -> Any:
    """
    Devuelve la clave apropiada según el algoritmo:
    - HS*: SECRET_KEY
    - RS*: JWKS (si JWT_JWKS_URL) o PEM público (si JWT_PUBLIC_KEY)
    """
    alg = (algorithm or "HS256").upper()

    if alg.startswith("HS"):
        if not SECRET_KEY:
            raise JoseCoreJWTError("SECRET_KEY ausente para algoritmos HS*.")
        return SECRET_KEY

    if alg.startswith("RS"):
        # 1) Preferimos JWKS si está definido
        if JWT_JWKS_URL:
            unverified_header = jose_jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            with httpx.Client(timeout=5.0) as client:
                jwks = client.get(JWT_JWKS_URL).json()
            key_to_use = None
            for key in jwks.get("keys", []):
                # Si no viene kid en el token, tomamos la primera clave válida
                if kid is None or key.get("kid") == kid:
                    key_to_use = key
                    break
            if not key_to_use:
                raise JoseCoreJWTError("No se encontró una JWK compatible (kid) en JWKS.")
            return key_to_use

        # 2) Si no hay JWKS, esperamos una clave pública PEM
        if JWT_PUBLIC_KEY:
            return JWT_PUBLIC_KEY

        raise JoseCoreJWTError("Falta JWT_JWKS_URL o JWT_PUBLIC_KEY para algoritmos RS*.")

    # Otros algoritmos no contemplados
    raise JoseCoreJWTError(f"Algoritmo no soportado: {alg}")


def _decode(token: str) -> Dict[str, Any]:
    """
    Decodifica el JWT aplicando la configuración disponible.
    - Verifica algoritmo/clave
    - Aplica 'leeway' vía options (python-jose), NO como kwarg suelto
    - Si se definieron issuer/audience, también los verifica
    - Permite tokens sin 'typ' si JWT_ACCEPT_TYPELESS=True (compat)
    """
    # Opciones de verificación: sólo exigimos aud/iss si están configuradas
    options = {
        "verify_signature": True,
        "verify_aud": bool(JWT_AUDIENCE),
        "verify_iss": bool(JWT_ISSUER),
        "require_exp": True,
        # 🔧 Aquí va el leeway correcto para python-jose:
        "leeway": int(JWT_LEEWAY_SECONDS or 0),
    }

    try:
        key = _resolve_key_for_decode(token, ALGORITHM)
        claims = jose_jwt.decode(
            token,
            key,
            algorithms=[(ALGORITHM or "HS256")],
            audience=JWT_AUDIENCE if JWT_AUDIENCE else None,
            issuer=JWT_ISSUER if JWT_ISSUER else None,
            options=options,
        )

        # Compat: si se exige 'typ' en otros servicios y aquí no viene,
        # lo toleramos si JWT_ACCEPT_TYPELESS=True.
        if not JWT_ACCEPT_TYPELESS:
            typ = claims.get("typ")
            if typ not in (None, "access", "bearer", "JWT"):
                # Si tuvieras una política estricta de tipos, ajusta aquí.
                pass

        return claims

    except (ExpiredSignatureError, JWTClaimsError, JoseCoreJWTError, JWTError):
        # Mantenemos tu manejo estándar de credenciales inválidas
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
