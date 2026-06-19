# backend/schemas/__init__.py
"""
📦 Paquete de esquemas (schemas) del backend.

Permite importar con:
    from backend.schemas import ChatRequest, IntentIn, UserCreate
"""

# 🗨️ Chat
from .chat import ChatRequest

# 🧠 Intents  (nombre real del archivo)
from .intent_schema import IntentIn, IntentOut, IntentsImport

# 👤 Usuarios
from .user_schema import UserCreate, UserOut, Rol

__all__ = [
    "ChatRequest",
    "IntentIn",
    "IntentOut",
    "IntentsImport",
    "UserCreate",
    "UserOut",
    "Rol",
]