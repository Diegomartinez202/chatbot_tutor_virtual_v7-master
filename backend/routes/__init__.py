# backend/routes/__init__.py
from fastapi import APIRouter

# Importa los routers de este paquete (usa imports relativos para evitar problemas de PYTHONPATH)
from . import (
    auth_routes as auth,
    chat,
    logs,
    stats,
    train,
    test_controller as test,
    user_controller as users,
    intent_controller as intents,
)

router = APIRouter()

# 🔐 Autenticación y perfil
router.include_router(auth.router, tags=["Auth"])

# 💬 Chat (proxy a Rasa) → vivirán bajo /api por el prefijo que aplica main.py
router.include_router(chat.router, tags=["Chat"])

# 📋 Logs (v1)
router.include_router(logs.router, prefix="/logs", tags=["Logs"])

# 📊 Estadísticas
router.include_router(stats.router, prefix="/admin", tags=["Estadísticas"])

# 🧠 Entrenamiento y Test
router.include_router(train.router, prefix="/admin", tags=["Entrenamiento"])
router.include_router(test.router, prefix="/admin", tags=["Test"])

# 👥 Usuarios (controlador moderno)
router.include_router(users.router, prefix="/admin", tags=["Usuarios"])

# ➕ Intents (controlador moderno)
router.include_router(intents.router, prefix="/admin", tags=["Intents"])