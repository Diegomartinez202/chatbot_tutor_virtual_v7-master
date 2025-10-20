# backend/routes/__init__.py

from fastapi import APIRouter

from backend.routes import (
    auth_routes as auth,
    chat,
    logs,
    stats,
    train,
    test_controller as test,
    user_controller as users,
    intent_controller as intents
)

router = APIRouter()

# 🔐 Autenticación y perfil
router.include_router(auth.router)

# 💬 Chat (proxy a Rasa)
router.include_router(chat.router, tags=["Chat"])

# 📋 Logs
router.include_router(logs.router, prefix="/logs", tags=["Logs"])

# 📊 Estadísticas
router.include_router(stats.router, prefix="/admin", tags=["Estadísticas"])

# 🧠 Entrenamiento y test
router.include_router(train.router, prefix="/admin", tags=["Entrenamiento"])
router.include_router(test.router, prefix="/admin", tags=["Test"])

# 👥 Usuarios
router.include_router(users.router, prefix="/admin", tags=["Usuarios"])

# ➕ Intents
router.include_router(intents.router, prefix="/admin", tags=["Intents"])