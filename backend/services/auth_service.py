# backend/services/auth_service.py
from backend.utils.logging import get_logger
from backend.services.log_service import log_access

logger = get_logger(__name__)


def registrar_login_exitoso(request, user):
    """Registra un login exitoso"""
    log_access(
        user_id=user["_id"],
        email=user["email"],
        rol=user.get("rol", "usuario"),
        endpoint=str(request.url.path),
        method=request.method,
        status=200,
        ip=request.state.ip,
        user_agent=request.state.user_agent
    )
    logger.info(f"🔐 Login exitoso para {user['email']} desde IP {request.state.ip}")


def registrar_acceso_perfil(request, user):
    """Registra acceso a perfil de usuario"""
    log_access(
        user_id=user["_id"],
        email=user["email"],
        rol=user.get("rol", "usuario"),
        endpoint=str(request.url.path),
        method=request.method,
        status=200,
        ip=request.state.ip,
        user_agent=request.state.user_agent
    )
    logger.info(f"👤 Perfil accedido por {user['email']} desde IP {request.state.ip}")


def registrar_logout(request, user):
    """Registra cierre de sesión"""
    log_access(
        user_id=user["_id"],
        email=user["email"],
        rol=user.get("rol", "usuario"),
        endpoint=str(request.url.path),
        method=request.method,
        status=200,
        ip=request.state.ip,
        user_agent=request.state.user_agent
    )
    logger.info(f"🚪 Logout de {user['email']} desde IP {request.state.ip}")


def registrar_refresh_token(request, user):
    """Registra generación de nuevo refresh token"""
    log_access(
        user_id=user["_id"],
        email=user["email"],
        rol=user.get("rol", "usuario"),
        endpoint=str(request.url.path),
        method=request.method,
        status=200,
        ip=request.state.ip,
        user_agent=request.state.user_agent
    )
    logger.info(f"🔄 Refresh token generado para {user['email']} desde IP {request.state.ip}")