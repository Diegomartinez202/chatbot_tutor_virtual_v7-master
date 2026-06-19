# backend/middleware/log_middleware.py
from __future__ import annotations

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from backend.middleware.request_id import get_request_id
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def _best_ip(request: Request) -> str | None:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.headers.get("x-real-ip") or (request.client.host if request.client else None)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware HTTP para:
      - Asegurar request.state.ip y request.state.user_agent si no los puso otro middleware.
      - Loguear método, ruta, status, duración y request-id.
      - NO bloquear la request si algo falla (logs nunca rompen la respuesta).
    """

    async def dispatch(self, request: Request, call_next):
        # Garantiza IP/UA si aún no fueron seteados por request_meta_middleware
        if not getattr(request.state, "ip", None):
            request.state.ip = _best_ip(request)
        if not getattr(request.state, "user_agent", None):
            request.state.user_agent = request.headers.get("user-agent", "")

        # Datos base
        rid = get_request_id()
        method = request.method
        path = request.url.path
        start = time.perf_counter()

        response = None
        try:
            response = await call_next(request)
            return response
        except Exception:
            # Log en error: devolvemos info útil para trazabilidad
            dur_ms = int((time.perf_counter() - start) * 1000)
            logger.exception(
                f"[{rid}] {method} {path} -> 500 ({dur_ms}ms) "
                f"ip={getattr(request.state, 'ip', None)} "
                f"ua={getattr(request.state, 'user_agent', '')}"
            )
            raise
        finally:
            try:
                status = getattr(response, "status_code", 500)
                dur_ms = int((time.perf_counter() - start) * 1000)

                # Usuario (si AuthMiddleware pobló request.state.user)
                user = getattr(request.state, "user", None)
                user_email = None
                if isinstance(user, dict):
                    user_email = user.get("email")
                elif user is not None:
                    # por si fuese objeto
                    user_email = getattr(user, "email", None)

                logger.info(
                    f"[{rid}] {method} {path} -> {status} ({dur_ms}ms) "
                    f"ip={getattr(request.state, 'ip', None)} "
                    f"ua={getattr(request.state, 'user_agent', '')} "
                    f"user={user_email or '-'}"
                )
            except Exception:
                # Nunca romper respuesta por fallo de logging
                pass