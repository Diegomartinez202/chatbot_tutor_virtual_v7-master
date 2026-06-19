# backend/controllers/__init__.py

# Reexporta routers con nombre claro para incluir en FastAPI
from .admin_controller import router as admin_router
from .user_controller import router as user_router

__all__ = ["admin_router", "user_router"]