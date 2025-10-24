from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from backend.db.mongodb import get_users_collection
from backend.config.settings import settings  # ✅ Importación actualizada

# ============================
# 🔐 CONFIGURACIÓN JWT
# ============================

SECRET_KEY = settings.secret_key
ALGORITHM = settings.jwt_algorithm  # ✅ Ahora usa settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes  # ✅ actualizado

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ============================
# 🎟️ CREAR TOKEN
# ============================

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ============================
# ❌ EXCEPCIÓN ESTÁNDAR
# ============================

def credentials_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

# ============================
# ✅ VERIFICAR TOKEN
# ============================

def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        rol = payload.get("rol")
        if user_id is None or rol is None:
            raise credentials_exception()
        return {
            "id": user_id,
            "email": email,
            "rol": rol
        }
    except JWTError:
        raise credentials_exception()

# ============================
# 🛡️ CONTROL DE ROL
# ============================

def require_role(allowed_roles: list):
    def role_checker(user: dict = Depends(verify_token)):
        if user["rol"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para acceder a este recurso"
            )
        return user
    return role_checker

# ============================
# 🙋 USUARIO ACTUAL (sin validar rol)
# ============================

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Extrae y retorna los datos del usuario autenticado desde el token JWT.
    """
    return verify_token(token)
