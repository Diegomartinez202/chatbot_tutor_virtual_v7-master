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
    # =========================================================
# 🔐 MIDDLEWARE AUTENTICACIÓN CON MODO DEMO ZAJUNA
# =========================================================

from fastapi import Request, HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config.settings import settings
from backend.services import jwt_service


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware que valida el token JWT o, si demo_mode=True,
    acepta el token FAKE_TOKEN_ZAJUNA para la sustentación.
    """

    async def dispatch(self, request: Request, call_next):
        # Extrae encabezado Authorization
        auth_header = request.headers.get("Authorization")
        scheme, token = get_authorization_scheme_param(auth_header)

        # 🔧 MODO DEMO: aceptar token simulado
        if settings.demo_mode:
            if token == jwt_service.FAKE_DEMO_TOKEN:
                request.state.user = jwt_service.FAKE_DEMO_CLAIMS
                response = await call_next(request)
                return response

        # Modo normal → verificar token real
        ok, claims = jwt_service.decode_token(auth_header)
        if not ok:
            raise HTTPException(status_code=401, detail="Token inválido o no autorizado")

        # Guardar usuario en request.state
        request.state.user = claims
        response = await call_next(request)
        return response