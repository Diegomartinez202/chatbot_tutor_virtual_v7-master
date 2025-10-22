from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import status
from fastapi.responses import JSONResponse

from backend.utils.jwt_manager import decode_token
from backend.config.settings import settings  
from backend.utils.logging import get_logger  

logger = get_logger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            try:
                decoded = decode_token(
                    token.split(" ")[1],
                    secret=settings.secret_key,       
                    algorithm=settings.jwt_algorithm  
                )
                request.state.user = decoded  # 👈 Se puede usar luego en access log
                logger.debug(f"Token válido para usuario: {decoded.get('email')}")
            except Exception as e:
                logger.warning(f"Token inválido: {str(e)}")
                # No se interrumpe la request; solo no se asigna user
        return await call_next(request)