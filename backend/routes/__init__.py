# =====================================================
# backend/routes/__init__.py
# =====================================================
from __future__ import annotations

from fastapi import APIRouter

# Router principal del backend
router = APIRouter()

# =====================================================
# Importacion de modulos de rutas (usar imports relativos
# para evitar circular imports durante la inicializacion
# del paquete backend.routes)
# =====================================================
from . import auth
from . import auth_tokens
from . import chat
from . import logs
from . import stats
from . import train
from . import test_controller
from . import user_controller
from . import intent_controller

# =====================================================
# Auth y Tokens
# =====================================================
router.include_router(auth.router, tags=["Auth"])
router.include_router(auth_tokens.router, tags=["Auth Tokens"])

# =====================================================
# Chat (proxy hacia Rasa)
# =====================================================
router.include_router(chat.router, tags=["Chat"])

# =====================================================
# Logs
# =====================================================
router.include_router(logs.router, prefix="/logs", tags=["Logs"])

# =====================================================
# Estadisticas
# =====================================================
router.include_router(stats.router, prefix="/admin", tags=["Estadisticas"])

# =====================================================
# Entrenamiento y Test
# =====================================================
router.include_router(train.router, prefix="/admin", tags=["Entrenamiento"])
router.include_router(test_controller.router, prefix="/admin", tags=["Test"])

# =====================================================
# Usuarios
# =====================================================
router.include_router(user_controller.router, prefix="/admin", tags=["Usuarios"])

# =====================================================
# Intents
# =====================================================
router.include_router(intent_controller.router, prefix="/admin", tags=["Intents"])

# Opcional: exponer el router desde el paquete
__all__ = ["router"]