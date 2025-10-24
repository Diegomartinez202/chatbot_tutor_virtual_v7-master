"""
📦 Modelos Pydantic del backend.

Centraliza todos los modelos de datos usados en controladores, servicios y respuestas de API.
Permite importar directamente desde backend.models sin necesidad de especificar cada archivo.

Ejemplo:
    from backend.models import UserOut, LogModel, MessageCreate
"""

from backend.models.auth_model import LoginRequest, TokenResponse
from backend.models.log_model import LogModel
from backend.models.message_model import MessageCreate
from backend.models.stats_model import (
    IntentMasUsado,
    UsuarioResumen,
    UsuarioPorRol,
    LogsPorDia,
    EstadisticasChatbotResponse,
)
from backend.models.test_log_model import TestLog
from backend.models.user_model import (
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