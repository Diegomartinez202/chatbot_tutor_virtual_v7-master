"""
📦 Paquete de esquemas (schemas) del backend.

Este módulo unifica los modelos de entrada/salida usados en controladores y servicios,
permitiendo importar fácilmente con:

    from backend.schemas import ChatRequest, IntentIn, UserCreate

Todos los esquemas están alineados con Pydantic v2.
"""

# 🗨️ Chat
from backend.schemas import ChatRequest

# 🧠 Intents
from backend.schemas import IntentIn, IntentOut, IntentsImport

# 👤 Usuarios
from backend.schemas import UserCreate, UserOut, Rol

__all__ = [
    # Chat
    "ChatRequest",

    # Intents
    "IntentIn",
    "IntentOut",
    "IntentsImport",

    # Usuarios
    "UserCreate",
    "UserOut",
    "Rol",
]