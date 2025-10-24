from pydantic import BaseModel, Field
from datetime import datetime

class LogModel(BaseModel):
    """🧾 Registro de eventos y actividad del usuario."""
    user_id: str = Field(..., description="ID del usuario")
    email: str = Field(..., description="Correo electrónico del usuario")
    rol: str = Field(..., description="Rol del usuario (admin, soporte, usuario)")
    endpoint: str = Field(..., description="Ruta del endpoint accedido")
    method: str = Field(..., description="Método HTTP utilizado")
    status: int = Field(..., description="Código de estado HTTP resultante")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Marca de tiempo del evento")
