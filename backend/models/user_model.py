from pydantic import BaseModel, Field, EmailStr
from enum import Enum
from typing import Optional

# 🎭 Enum para roles del sistema
class RolEnum(str, Enum):
    admin = "admin"
    soporte = "soporte"
    usuario = "usuario"

# 📥 Login de usuario
class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="admin@example.com", description="Correo electrónico del usuario")
    password: str = Field(..., min_length=4, example="1234", description="Contraseña del usuario")

# 🔑 Token JWT
class UserToken(BaseModel):
    sub: str = Field(..., description="Identificador único del sujeto (usuario)")
    exp: int = Field(..., description="Fecha de expiración en formato UNIX")

# 📤 Respuesta pública del usuario (por ejemplo, /auth/me)
class UserResponse(BaseModel):
    id: str = Field(..., example="64f1a8b2e6a1d23c5e123456")
    email: EmailStr = Field(..., example="usuario@correo.com")
    rol: RolEnum = Field(default=RolEnum.usuario, example="usuario")

# 📋 Modelo para panel de administración
class UserOut(BaseModel):
    id: str
    nombre: str
    email: EmailStr
    rol: RolEnum

# ✏️ Modelo para actualizar usuarios
class UserUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, description="Nuevo nombre del usuario")
    email: Optional[EmailStr] = Field(default=None, description="Nuevo correo electrónico")
    rol: Optional[RolEnum] = Field(default=None, description="Nuevo rol del usuario")
