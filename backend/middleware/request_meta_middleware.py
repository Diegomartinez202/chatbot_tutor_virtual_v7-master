#\backend\middleware\request_meta_middleware.py
from __future__ import annotations

from typing import Awaitable, Callable, Optional

from fastapi import Request
from starlette.responses import Response

def _best_ip(request: Request) -> Optional[str]:
    """
    Determina la IP 'real' del cliente:
    - Prioriza X-Forwarded-For (primer IP)
    - Luego X-Real-IP
    - Finalmente request.client.host
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.headers.get("x-real-ip") or (request.client.host if request.client else None)

async def request_meta_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """
    Middleware simple (funcional) que puebla:
      - request.state.ip
      - request.state.user_agent
    para que el resto del stack (logs, servicios) no tenga que calcularlo.
    """
    request.state.ip = _best_ip(request)
    request.state.user_agent = request.headers.get("user-agent", "")

    response = await call_next(request)
    return response