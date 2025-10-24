from typing import Annotated
from pydantic import BaseModel, EmailStr, Field, ConfigDict, StringConstraints
from enum import Enum

class Rol(str, Enum):
    admin = "admin"
    soporte = "soporte"
    usuario = "usuario"

class UserCreate(BaseModel):
    """
    Esquema para registrar un nuevo usuario.
    """
    nombre: Annotated[str, StringConstraints(min_length=2, max_length=50)] = Field(..., description="Nombre del usuario")
    email: EmailStr = Field(..., description="Correo electrónico válido")
    rol: Rol = Field(..., description="Rol permitido: admin, soporte, usuario")
    password: Annotated[str, StringConstraints(min_length=8)] = Field(..., description="Contraseña con mínimo 8 caracteres")

class UserOut(BaseModel):
    """
    Esquema para retornar información de usuario (sin contraseña).
    """
    id: str = Field(..., alias="_id")
    nombre: str
    email: EmailStr
    rol: Rol

    model_config = ConfigDict(validate_by_name=True)
