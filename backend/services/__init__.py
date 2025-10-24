"""
⚙️ Servicios del backend.

Reúne las funciones y utilidades principales que interactúan con
la base de datos, autenticación, Rasa y notificaciones.

Ejemplo:
    from backend.services import jwt_service, log_service, email_service
"""

from backend.services import (
    jwt_service,
    log_service,
    email_service,
    intent_manager,
    stats_service,
    rasa_proxy_service,
)

__all__ = [
    "jwt_service",
    "log_service",
    "email_service",
    "intent_manager",
    "stats_service",
    "rasa_proxy_service",
]