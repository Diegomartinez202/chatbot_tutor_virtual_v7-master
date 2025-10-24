# backend/services/__init__.py
"""
⚙️ Servicios del backend (cargador perezoso anti-ciclos).

Puedes seguir importando así:
    from backend.services import stats_service
    from backend.services import log_service

O directamente por módulo:
    import backend.services.stats_service as stats_service
"""

import importlib
import types

# Mapa de alias → módulo real
_MODULES = {
    "jwt_service": "backend.services.jwt_service",
    "log_service": "backend.services.log_service",
    "email_service": "backend.services.email_service",
    "intent_manager": "backend.services.intent_manager",
    "stats_service": "backend.services.stats_service",
    "rasa_proxy_service": "backend.services.rasa_proxy_service",
    "user_service": "backend.services.user_service",
    "auth_service": "backend.services.auth_service",
    "chat_service": "backend.services.chat_service",
    "train_service": "backend.services.train_service",
}

__all__ = list(_MODULES.keys())

def __getattr__(name: str) -> types.ModuleType:
    mod_path = _MODULES.get(name)
    if not mod_path:
        raise AttributeError(f"module 'backend.services' has no attribute '{name}'")
    mod = importlib.import_module(mod_path)
    globals()[name] = mod
    return mod