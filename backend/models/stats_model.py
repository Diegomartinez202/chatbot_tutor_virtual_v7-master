from pydantic import BaseModel, Field
from typing import List, Optional

class IntentMasUsado(BaseModel):
    intent: str = Field(..., description="Nombre del intent")
    total: int = Field(..., description="Número de veces utilizado")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "extra": "ignore",
    }

class UsuarioResumen(BaseModel):
    id: str = Field(..., description="ID del usuario")
    email: str = Field(..., description="Correo electrónico")
    rol: Optional[str] = Field(default="usuario", description="Rol del usuario")
    nombre: Optional[str] = Field(default="", description="Nombre del usuario")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "extra": "ignore",
    }

class UsuarioPorRol(BaseModel):
    rol: str = Field(..., description="Rol del usuario")
    total: int = Field(..., description="Cantidad de usuarios con ese rol")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "extra": "ignore",
    }

class LogsPorDia(BaseModel):
    fecha: str = Field(..., description="Fecha en formato YYYY-MM-DD")
    total: int = Field(..., description="Cantidad de logs ese día")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "extra": "ignore",
    }

class EstadisticasChatbotResponse(BaseModel):
    """📊 Respuesta general de estadísticas del chatbot."""
    total_logs: int
    total_exportaciones_csv: int
    intents_mas_usados: List[IntentMasUsado]
    total_usuarios: int
    ultimos_usuarios: List[UsuarioResumen]
    usuarios_por_rol: List[UsuarioPorRol]
    logs_por_dia: List[LogsPorDia]

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "extra": "ignore",
    }