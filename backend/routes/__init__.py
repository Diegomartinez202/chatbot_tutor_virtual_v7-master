# =====================================================
# 🧩 backend/routes/__init__.py
# =====================================================
from __future__ import annotations
from fastapi import APIRouter

# Router principal del backend
router = APIRouter()

# =====================================================
# 🔐 Importación de módulos de rutas (coinciden con tus archivos reales)
# =====================================================
from backend.routes import (
    auth,                # <— tu archivo es backend/routes/auth.py
    auth_tokens,
    chat,
    logs,
    stats,
    train,
    test_controller,
    user_controller,
    intent_controller,
)

# =====================================================
# 🔐 Autenticación y Tokens
# =====================================================
router.include_router(auth.router, tags=["Auth"])
router.include_router(auth_tokens.router, tags=["Auth Tokens"])

# =====================================================
# 💬 Chat (proxy hacia Rasa)
# =====================================================
router.include_router(chat.router, tags=["Chat"])

# =====================================================
# 📋 Logs
# =====================================================
router.include_router(logs.router, prefix="/logs", tags=["Logs"])

# =====================================================
# 📊 Estadísticas
# =====================================================
router.include_router(stats.router, prefix="/admin", tags=["Estadísticas"])

# =====================================================
# 🧠 Entrenamiento y Test
# =====================================================
router.include_router(train.router, prefix="/admin", tags=["Entrenamiento"])
router.include_router(test_controller.router, prefix="/admin", tags=["Test"])

# =====================================================
# 👥 Usuarios
# =====================================================
router.include_router(user_controller.router, prefix="/admin", tags=["Usuarios"])

# =====================================================
# ➕ Intents
# =====================================================
router.include_router(intent_controller.router, prefix="/admin", tags=["Intents"])