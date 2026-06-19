from typing import Annotated
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, ConfigDict, StringConstraints

class Rol(str, Enum):
    """🎭 Roles permitidos en el sistema."""
    admin = "admin"
    soporte = "soporte"
    usuario = "usuario"
    estudiante = "estudiante"
    invitado = "invitado"
class UserCreate(BaseModel):
    """
    📥 Esquema para registrar un nuevo usuario.
    """
    nombre: Annotated[str, StringConstraints(min_length=2, max_length=50)] = Field(
        ..., description="Nombre del usuario"
    )
    email: EmailStr = Field(..., description="Correo electrónico válido")
    rol: Rol = Field(..., description="Rol permitido: admin, soporte, usuario")
    password: Annotated[str, StringConstraints(min_length=8)] = Field(
        ..., description="Contraseña con mínimo 8 caracteres"
    )

    model_config = ConfigDict(
        validate_by_name=True,
        from_attributes=True,
        populate_by_name=True,
        extra="ignore",
    )

class UserOut(BaseModel):
    """
    📤 Esquema para retornar información de usuario (sin contraseña).
    """
    id: str = Field(..., alias="_id", description="Identificador único del usuario")
    nombre: str = Field(..., description="Nombre completo del usuario")
    email: EmailStr = Field(..., description="Correo electrónico")
    rol: Rol = Field(..., description="Rol asignado al usuario")

    model_config = ConfigDict(
        validate_by_name=True,
        from_attributes=True,
        populate_by_name=True,
        extra="ignore",
    )