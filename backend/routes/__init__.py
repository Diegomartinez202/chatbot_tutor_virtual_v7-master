# backend/routes/__init__.py
from __future__ import annotations
from fastapi import APIRouter

router = APIRouter()

# Auth principal y tokens
from . import auth
from . import auth_tokens

# Chat (api_chat.router, chat.chat_router)
from . import api_chat
from . import chat as chat_module

# Logs / Stats / Train
from . import logs
from . import stats
from . import train

# Intents (asegúrate que el archivo se llame intent_controller.py)
from . import intent_controller

# Usuarios (opcional)
try:
    from . import user_controller as users_module
except Exception:
    users_module = None

# Tests (desde backend/test)
try:
    from backend.test import test_controller as test_module
except Exception:
    test_module = None

# 🔐 Auth
router.include_router(auth.router, tags=["Auth"])
router.include_router(auth_tokens.router, tags=["Auth Tokens"])

# 💬 Chat
router.include_router(api_chat.router, tags=["Chat"])
router.include_router(chat_module.chat_router, tags=["Chat"])

# 📋 Logs
router.include_router(logs.router, prefix="/logs", tags=["Logs"])

# 📊 Estadísticas
router.include_router(stats.router, prefix="/admin", tags=["Estadísticas"])

# 🧠 Entrenamiento
router.include_router(train.router, prefix="/admin", tags=["Entrenamiento"])

# 🧪 Tests
if test_module and hasattr(test_module, "router"):
    router.include_router(test_module.router, prefix="/admin", tags=["Test"])

# 👥 Usuarios
if users_module and hasattr(users_module, "router"):
    router.include_router(users_module.router, prefix="/admin", tags=["Usuarios"])

# ➕ Intents
router.include_router(intent_controller.router, prefix="/admin", tags=["Intents"])