from pydantic import BaseModel, Field
from typing import List, Optional


class IntentMasUsado(BaseModel):
    intent: str
    total: int


class UsuarioResumen(BaseModel):
    id: str
    email: str
    rol: Optional[str] = "usuario"
    nombre: Optional[str] = ""


class UsuarioPorRol(BaseModel):
    rol: str
    total: int


class LogsPorDia(BaseModel):
    fecha: str  # formato YYYY-MM-DD
    total: int


class EstadisticasChatbotResponse(BaseModel):
    total_logs: int
    total_exportaciones_csv: int
    intents_mas_usados: List[IntentMasUsado]
    total_usuarios: int
    ultimos_usuarios: List[UsuarioResumen]
    usuarios_por_rol: List[UsuarioPorRol]
    logs_por_dia: List[LogsPorDia]