from pydantic import BaseModel, Field
from datetime import datetime

class TestLog(BaseModel):
    """🧪 Registro de pruebas automáticas o diagnósticos."""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Fecha y hora de la prueba")
    test_name: str = Field(..., description="Nombre de la prueba ejecutada")
    result: str = Field(..., description="Resultado descriptivo de la prueba")
    success: bool = Field(..., description="Indicador de éxito o fallo")