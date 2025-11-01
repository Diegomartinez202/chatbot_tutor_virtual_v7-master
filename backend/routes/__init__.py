# backend/routes/__init__.py
from __future__ import annotations

import os
from fastapi import APIRouter
from . import auth
from . import auth_tokens
from . import api_chat
from . import chat as chat_module
from . import logs
from . import stats
from . import train
from . import link_preview as link_preview_module
from . import telemetry as telemetry_module
from . import voice
# Intents (controlador nuevo, rutas ya incluyen /admin/…)
from . import intent_controller
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
# Crea el router principal antes de incluir subrouters
router = APIRouter()
router.include_router(chat_module.chat_router, tags=["Chat"])
# ─────────────────────────────────────────────────────
# Incluir routers
# ─────────────────────────────────────────────────────

# 🔐 Auth
router.include_router(auth.router, tags=["Auth"])
router.include_router(auth_tokens.router, tags=["Auth Tokens"])

# 📋 Logs
router.include_router(logs.router, prefix="/logs", tags=["Logs"])
router.include_router(voice.router)
# 📊 Estadísticas
router.include_router(stats.router, prefix="/admin", tags=["Estadísticas"])

# 🧠 Entrenamiento
router.include_router(train.router, prefix="/admin", tags=["Entrenamiento"])

router.include_router(link_preview_module.router)
router.include_router(telemetry_module.router)
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


