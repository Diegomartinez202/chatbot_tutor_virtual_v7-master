# backend/middleware/access_log_middleware.py
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from backend.services.log_service import log_access_middleware

class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        user = getattr(request.state, "user", None)
        ip = getattr(request.state, "ip", None) or (request.client.host if request.client else None)
        ua = getattr(request.state, "user_agent", None) or request.headers.get("user-agent")

        try:
            log_access_middleware(
                endpoint=str(request.url.path),
                method=request.method,
                status=response.status_code,
                ip=ip,
                user_agent=ua,
                user=user,
            )
        except Exception:
            # Nunca romper respuesta por fallo de logging
            pass

        return response