# backend/routes/__init__.py
from __future__ import annotations

import os
from fastapi import APIRouter

# Crea el router principal antes de incluir subrouters
router = APIRouter()

# ─────────────────────────────────────────────────────
# Importa módulos por su nombre real
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

# Intents (controlador nuevo, rutas ya incluyen /admin/…)
from . import intent_controller
from . import chat

# Usuarios (opcional si existe un router en backend/routes/)
try:
    from . import user_controller as users_module
except Exception:
    users_module = None

# Tests (tu archivo está en backend/test/test_controller.py)
try:
    from backend.test import test_controller as test_module
except Exception:
    test_module = None

# Legacy intents (opcional y condicional para compatibilidad)
ENABLE_INTENT_LEGACY = os.getenv("ENABLE_INTENT_LEGACY", "false").lower() == "true"
if ENABLE_INTENT_LEGACY:
    try:
        from . import intent_legacy_controller as intent_legacy
    except Exception:
        intent_legacy = None
else:
    intent_legacy = None

# ─────────────────────────────────────────────────────
# Incluir routers
# ─────────────────────────────────────────────────────

# 🔐 Auth
router.include_router(auth.router, tags=["Auth"])
router.include_router(auth_tokens.router, tags=["Auth Tokens"])
router.include_router(chat.router)
# 📋 Logs
router.include_router(logs.router, prefix="/logs", tags=["Logs"])

# 📊 Estadísticas
router.include_router(stats.router, prefix="/admin", tags=["Estadísticas"])

# 🧠 Entrenamiento
router.include_router(train.router, prefix="/admin", tags=["Entrenamiento"])

# 🧪 Tests (opcional si existe)
if test_module and hasattr(test_module, "router"):
    router.include_router(test_module.router, prefix="/admin", tags=["Test"])

# 👥 Usuarios (opcional si existe)
if users_module and hasattr(users_module, "router"):
    router.include_router(users_module.router, prefix="/admin", tags=["Usuarios"])

# ➕ Intents (NO añadir prefix aquí: las rutas ya comienzan con /admin)
router.include_router(intent_controller.router, tags=["Intents"])

# ➕ Intents Legacy (solo si se habilita por ENV)
if intent_legacy and hasattr(intent_legacy, "router"):
    router.include_router(intent_legacy.router, tags=["Intents Legacy"])


