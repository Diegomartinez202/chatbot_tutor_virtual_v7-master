# =====================================================
# 🧩 backend/services/auth_service.py
# =====================================================
from __future__ import annotations

from typing import Optional, Dict, Any

from backend.utils.logging import get_logger
# ⬇️ Usar el logger real que enviaste (audit_logger)
from backend.services.audit_logger import log_access
from backend.services.user_service import (
    verify_user_credentials,
    get_user_by_email,  # (conservamos por compat si lo usas en otro lado)
)

logger = get_logger(__name__)


def _sanitize_email(email: str) -> str:
    return (email or "").strip().lower()


# =====================================================
# 🔐 Autenticación
# =====================================================
def login_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Valida credenciales y retorna el usuario si son correctas.
    - Normaliza el email
    - Usa verify_user_credentials del user_service
    - Elimina el campo 'password' del dict antes de retornar
    """
    try:
        email_norm = _sanitize_email(email)
        user = verify_user_credentials(email_norm, password)
        if not user:
            logger.warning(f"[auth_service] Login fallido para {email_norm}")
            return None

        # Asegurar consistencia (_id como str y sin password)
        if "_id" in user and not isinstance(user["_id"], str):
            try:
                user["_id"] = str(user["_id"])
            except Exception:
                pass
        user.pop("password", None)
        return user
    except Exception as e:
        logger.error(f"[auth_service] Error en login_user({email}): {e}")
        return None


# =====================================================
# 📝 Registro de eventos (se mantiene tu lógica)
# =====================================================
def registrar_login_exitoso(request, user: Dict[str, Any]) -> None:
    """Registra un login exitoso en logs de acceso."""
    try:
        log_access(
            user_id=user.get("_id") or user.get("id"),
            email=user.get("email", ""),
            rol=user.get("rol", "usuario"),
            endpoint=str(getattr(request, "url", getattr(request, "url", ""))).split("?")[0] if getattr(request, "url", None) else str(getattr(request, "scope", {}).get("path", "")),
            method=getattr(request, "method", "GET"),
            status=200,
            ip=getattr(getattr(request, "state", None), "ip", None),
            user_agent=getattr(getattr(request, "state", None), "user_agent", None),
        )
        logger.info(
            f"🔐 Login exitoso para {user.get('email')} desde IP {getattr(getattr(request, 'state', None), 'ip', '-')}"
        )
    except Exception as e:
        logger.warning(f"[auth_service] No se pudo registrar login exitoso: {e}")


def registrar_acceso_perfil(request, user: Dict[str, Any]) -> None:
    """Registra acceso a perfil de usuario."""
    try:
        log_access(
            user_id=user.get("_id") or user.get("id"),
            email=user.get("email", ""),
            rol=user.get("rol", "usuario"),
            endpoint=str(getattr(request, "url", getattr(request, "url", ""))).split("?")[0] if getattr(request, "url", None) else str(getattr(request, "scope", {}).get("path", "")),
            method=getattr(request, "method", "GET"),
            status=200,
            ip=getattr(getattr(request, "state", None), "ip", None),
            user_agent=getattr(getattr(request, "state", None), "user_agent", None),
        )
        logger.info(
            f"👤 Perfil accedido por {user.get('email')} desde IP {getattr(getattr(request, 'state', None), 'ip', '-')}"
        )
    except Exception as e:
        logger.warning(f"[auth_service] No se pudo registrar acceso a perfil: {e}")


def registrar_logout(request, user: Dict[str, Any]) -> None:
    """Registra cierre de sesión."""
    try:
        log_access(
            user_id=user.get("_id") or user.get("id"),
            email=user.get("email", ""),
            rol=user.get("rol", "usuario"),
            endpoint=str(getattr(request, "url", getattr(request, "url", ""))).split("?")[0] if getattr(request, "url", None) else str(getattr(request, "scope", {}).get("path", "")),
            method=getattr(request, "method", "GET"),
            status=200,
            ip=getattr(getattr(request, "state", None), "ip", None),
            user_agent=getattr(getattr(request, "state", None), "user_agent", None),
        )
        logger.info(
            f"🚪 Logout de {user.get('email')} desde IP {getattr(getattr(request, 'state', None), 'ip', '-')}"
        )
    except Exception as e:
        logger.warning(f"[auth_service] No se pudo registrar logout: {e}")


def registrar_refresh_token(request, user: Dict[str, Any]) -> None:
    """Registra generación de nuevo refresh token."""
    try:
        log_access(
            user_id=user.get("_id") or user.get("id"),
            email=user.get("email", ""),
            rol=user.get("rol", "usuario"),
            endpoint=str(getattr(request, "url", getattr(request, "url", ""))).split("?")[0] if getattr(request, "url", None) else str(getattr(request, "scope", {}).get("path", "")),
            method=getattr(request, "method", "GET"),
            status=200,
            ip=getattr(getattr(request, "state", None), "ip", None),
            user_agent=getattr(getattr(request, "state", None), "user_agent", None),
        )
        logger.info(
            f"🔄 Refresh token generado para {user.get('email')} desde IP {getattr(getattr(request, 'state', None), 'ip', '-')}"
        )
    except Exception as e:
        logger.warning(f"[auth_service] No se pudo registrar refresh token: {e}")