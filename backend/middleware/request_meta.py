# backend/middleware/request_meta.py
from fastapi import Request
from typing import Callable, Awaitable

async def request_meta_middleware(request: Request, call_next: Callable[[Request], Awaitable]):
    # IP real: primero X-Forwarded-For (proxy), si no X-Real-IP, si no client.host
    xff = request.headers.get("x-forwarded-for")
    if xff:
        ip = xff.split(",")[0].strip()
    else:
        ip = request.headers.get("x-real-ip") or (request.client.host if request.client else None)

    ua = request.headers.get("user-agent", "")

    # expón a los handlers
    request.state.ip = ip
    request.state.user_agent = ua

    response = await call_next(request)
    return response