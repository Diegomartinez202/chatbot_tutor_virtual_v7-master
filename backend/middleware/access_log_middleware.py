# backend/middleware/access_log_middleware.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from backend.services.log_service import log_access_middleware

class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        user = getattr(request.state, "user", None)  # ✅ Más limpio

        log_access_middleware(
            endpoint=str(request.url.path),
            method=request.method,
            status=response.status_code,
            ip=request.client.host,
            user_agent=request.headers.get("user-agent"),
            user=user
        )
        return response
