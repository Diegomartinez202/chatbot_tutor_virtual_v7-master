# backend/services/auth_service.py

from backend.logger import logger
from backend.services.log_service import log_access

def registrar_login_exitoso(request, user):
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
