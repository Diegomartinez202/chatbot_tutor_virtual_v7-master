from pydantic import BaseModel, EmailStr, constr, Field
from enum import Enum

# ============================
# 🔐 Enum con roles válidos
# ============================
class Rol(str, Enum):
    admin = "admin"
    soporte = "soporte"
    usuario = "usuario"

# ============================
# 🧾 Esquema para registro
# ============================
class UserCreate(BaseModel):
    """
    Esquema para registrar un nuevo usuario.
    """
    nombre: str = Field(..., min_length=2, max_length=50, description="Nombre del usuario")
    email: EmailStr = Field(..., description="Correo electrónico válido")
    rol: Rol = Field(..., description="Rol permitido: admin, soporte, usuario")
    password: constr(min_length=8) = Field(..., description="Contraseña con mínimo 8 caracteres")

# ============================
# 👤 Esquema para respuesta sin contraseña
# ============================
class UserOut(BaseModel):
    """
    Esquema para retornar información de usuario (sin contraseña).
    """
    id: str = Field(..., alias="_id")  # 🔁 Convierte automáticamente el ObjectId a str y lo renombra a "id"
    nombre: str
    email: EmailStr
    rol: Rol

    class Config:
        allow_population_by_field_name = True  # ✅ Permite usar .dict(by_alias=True)