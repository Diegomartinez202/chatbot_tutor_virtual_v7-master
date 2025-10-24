"""
📦 Modelos Pydantic del backend.

Centraliza todos los modelos de datos usados en controladores, servicios y respuestas de API.
Permite importar directamente desde backend.models sin necesidad de especificar cada archivo.

Ejemplo:
    from backend.models import UserOut, LogModel, MessageCreate
"""

from backend.models import LoginRequest, TokenResponse
from backend.models import LogModel
from backend.models import MessageCreate
from backend.models import (
    IntentMasUsado,
    UsuarioResumen,
    UsuarioPorRol,
    LogsPorDia,
    EstadisticasChatbotResponse,
)
from backend.models import TestLog
from backend.models import (
    RolEnum,
    UserLogin,
    UserToken,
    UserResponse,
    UserOut,
    UserUpdate,
)

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "LogModel",
    "MessageCreate",
    "IntentMasUsado",
    "UsuarioResumen",
    "UsuarioPorRol",
    "LogsPorDia",
    "EstadisticasChatbotResponse",
    "TestLog",
    "RolEnum",
    "UserLogin",
    "UserToken",
    "UserResponse",
    "UserOut",
    "UserUpdate",
]