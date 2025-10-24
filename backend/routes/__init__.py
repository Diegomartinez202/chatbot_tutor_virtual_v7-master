# =====================================================
# 🧩 backend/routes/__init__.py
# =====================================================
from __future__ import annotations
from fastapi import APIRouter

router = APIRouter()

# ─────────────────────────────────────────────────────
# Importa módulos CON SUS NOMBRES REALES (sin crear alias
# que cambien atributos). Cada módulo define su propio
# APIRouter local y aquí solo lo agregamos.
# ─────────────────────────────────────────────────────

# Auth principal y tokens
from . import auth
from . import auth_tokens

# Chat:
# - api_chat: define `router` (prefijo /api)
# - chat:     define `chat_router` (prefijo /chat)
from . import api_chat
from . import chat as chat_module

# Logs / Stats / Train
from . import logs
from . import stats
from . import train

# Intents (asegúrate que el archivo se llama EXACTAMENTE intent_controller.py)
from . import intent_controller

# Usuarios (si tienes controlador de rutas de usuarios en backend/routes/)
# Si en tu repo está en backend/controllers/user_controller.py, NO lo importes aquí.
try:
    from . import user_controller as users_module  # backend/routes/user_controller.py
except Exception:
    users_module = None

# Tests (tu archivo está en backend/test/test_controller.py)
# Lo importamos de su ubicación real para evitar circularidad.
try:
    from backend.test import test_controller as test_module
except Exception:
    test_module = None

# ─────────────────────────────────────────────────────
# Incluir routers
# ─────────────────────────────────────────────────────

# 🔐 Auth
router.include_router(auth.router, tags=["Auth"])
router.include_router(auth_tokens.router, tags=["Auth Tokens"])

# 💬 Chat
# /api/chat (proxy a Rasa)
router.include_router(api_chat.router, tags=["Chat"])
# /chat/* (health, debug, post hacia service local)
router.include_router(chat_module.chat_router, tags=["Chat"])

# 📋 Logs
router.include_router(logs.router, prefix="/logs", tags=["Logs"])

# 📊 Estadísticas (quedan bajo /admin/* dentro del propio stats.router)
router.include_router(stats.router, prefix="/admin", tags=["Estadísticas"])

# 🧠 Entrenamiento
router.include_router(train.router, prefix="/admin", tags=["Entrenamiento"])

# 🧪 Tests (opcional si existe)
if test_module and hasattr(test_module, "router"):
    router.include_router(test_module.router, prefix="/admin", tags=["Test"])

# 👥 Usuarios (opcional si existe en routes/)
if users_module and hasattr(users_module, "router"):
    router.include_router(users_module.router, prefix="/admin", tags=["Usuarios"])

# ➕ Intents
router.include_router(intent_controller.router, prefix="/admin", tags=["Intents"])