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
from . import health_status as health_status_module
from . import intent_controller

try:
    from . import user_controller as users_module
except Exception:
    users_module = None

try:
    from backend.test import test_controller as test_module
except Exception:
    test_module = None

ENABLE_INTENT_LEGACY = os.getenv("ENABLE_INTENT_LEGACY", "false").lower() == "true"
if ENABLE_INTENT_LEGACY:
    try:
        from . import intent_legacy_controller as intent_legacy
    except Exception:
        intent_legacy = None
else:
    intent_legacy = None

router = APIRouter()

# ─────────────────────────────────────────────────────
# Chat
# ─────────────────────────────────────────────────────
# 1) Incluimos el router "global" de chat.py (trae /health, /chat/health, etc.)
router.include_router(chat_module.router)

# 2) Incluimos el subrouter /chat con tag "Chat"
router.include_router(chat_module.chat_router, tags=["Chat"])

# ─────────────────────────────────────────────────────
# Otros routers
# ─────────────────────────────────────────────────────

router.include_router(auth.router, tags=["Auth"])
router.include_router(auth_tokens.router, tags=["Auth Tokens"])

router.include_router(logs.router, prefix="/logs", tags=["Logs"])
router.include_router(voice.router)

router.include_router(stats.router, prefix="/admin", tags=["Estadísticas"])
router.include_router(train.router, prefix="/admin", tags=["Entrenamiento"])

router.include_router(link_preview_module.router)
router.include_router(telemetry_module.router)

if test_module and hasattr(test_module, "router"):
    router.include_router(test_module.router, prefix="/admin", tags=["Test"])

if users_module and hasattr(users_module, "router"):
    router.include_router(users_module.router, prefix="/admin", tags=["Usuarios"])

router.include_router(intent_controller.router, tags=["Intents"])

if intent_legacy and hasattr(intent_legacy, "router"):
    router.include_router(intent_legacy.router, tags=["Intents Legacy"])

# Montamos el router de health_status con un prefix para no tocar /health raíz
if health_status_module and hasattr(health_status_module, "router"):
    router.include_router(health_status_module.router, prefix="/health", tags=["Health"])
