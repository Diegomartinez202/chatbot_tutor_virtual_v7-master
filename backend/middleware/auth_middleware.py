# backend/middleware/auth_middleware.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import status
from backend.utils.jwt_manager import decode_token
from fastapi.responses import JSONResponse

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            try:
                decoded = decode_token(token.split(" ")[1])
                request.state.user = decoded  # 👈 Se usará luego en access log
            except Exception:
                pass  # Token inválido, se puede ignorar o registrar
        return await call_next(request)