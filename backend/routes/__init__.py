# backend/routes/__init__.py

from fastapi import APIRouter

# Importa los routers de este paquete (usa imports relativos para evitar problemas de PYTHONPATH)
from . import (
    auth_routes as auth,
    auth_tokens,                 # 🔐 nuevo módulo unificado (refresh, logout, token)
    chat,
    logs,
    stats,
    train,
    test_controller as test,
    user_controller as users,
    intent_controller as intents,
)

router = APIRouter()

# ===========================
# 🔐 Autenticación y Tokens
# ===========================
# Auth principal (login + perfil)
router.include_router(auth.router, tags=["Auth"])
# Tokens (login alternativo, refresh, logout)
router.include_router(auth_tokens.router, tags=["Auth Tokens"])

# ===========================
# 💬 Chat (proxy a Rasa)
# ===========================
router.include_router(chat.router, tags=["Chat"])

# ===========================
# 📋 Logs
# ===========================
router.include_router(logs.router, prefix="/logs", tags=["Logs"])

# ===========================
# 📊 Estadísticas
# ===========================
router.include_router(stats.router, prefix="/admin", tags=["Estadísticas"])

# ===========================
# 🧠 Entrenamiento y Test
# ===========================
router.include_router(train.router, prefix="/admin", tags=["Entrenamiento"])
router.include_router(test.router, prefix="/admin", tags=["Test"])

# ===========================
# 👥 Usuarios
# ===========================
router.include_router(users.router, prefix="/admin", tags=["Usuarios"])

# ===========================
# ➕ Intents
# ===========================
router.include_router(intents.router, prefix="/admin", tags=["Intents"])