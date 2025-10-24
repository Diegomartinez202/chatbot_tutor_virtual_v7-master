from __future__ import annotations

from typing import Callable
from uuid import uuid4
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

# ContextVar para leer el request-id desde cualquier parte del código
REQUEST_ID_CTX_KEY: ContextVar[str] = ContextVar("request_id", default="-")

def get_request_id() -> str:
    """Devuelve el request-id actual (o '-' si no hay uno activo)."""
    return REQUEST_ID_CTX_KEY.get()

class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Asegura que cada request tenga un X-Request-ID.
    - Si el cliente lo envía, lo reutiliza.
    - Si no, genera un UUID4.
    - Lo expone en el contexto (ContextVar) y lo devuelve en la respuesta.
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        incoming = request.headers.get(self.header_name)
        rid = incoming or str(uuid4())

        # Guarda en contexto para logging y trazabilidad
        token = REQUEST_ID_CTX_KEY.set(rid)
        try:
            response = await call_next(request)
        finally:
            # Limpieza del contexto aunque falle la request
            REQUEST_ID_CTX_KEY.reset(token)

        # Devuelve siempre el header al cliente
        response.headers[self.header_name] = rid
        return response