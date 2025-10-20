from pydantic import BaseModel, Field, EmailStr
from enum import Enum

# 🎭 Enum para roles definidos del sistema
class RolEnum(str, Enum):
    admin = "admin"
    soporte = "soporte"
    usuario = "usuario"

# 🔐 Login: entrada
class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="admin@example.com")
    password: str = Field(..., min_length=4, example="1234")

# 🔐 Token JWT: payload esperado
class UserToken(BaseModel):
    sub: str  # sub es el estándar en JWT para identificar al sujeto
    exp: int

# 📤 Respuesta pública (ej: /auth/me)
class UserResponse(BaseModel):
    id: str = Field(..., example="64f1a8b2e6a1d23c5e123456")
    email: EmailStr = Field(..., example="usuario@correo.com")
    rol: RolEnum = Field(default=RolEnum.usuario, example="usuario")

# 📋 Modelo usado para panel de administración
class UserOut(BaseModel):
    id: str
    nombre: str
    email: EmailStr
    rol: RolEnum
# ✏️ Modelo para actualizar usuarios
class UserUpdate(BaseModel):
    nombre: str | None = None
    email: EmailStr | None = None
    rol: RolEnum | None = None