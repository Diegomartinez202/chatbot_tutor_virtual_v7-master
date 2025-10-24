# backend/middleware/request_id.py
from typing import Callable
from uuid import uuid4
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.middleware.base import BaseHTTPMiddleware
from contextvars import ContextVar

REQUEST_ID_CTX_KEY: ContextVar[str] = ContextVar("request_id", default="-")

def get_request_id() -> str:
    return REQUEST_ID_CTX_KEY.get()

class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request, call_next: Callable):
        incoming = request.headers.get(self.header_name)
        rid = incoming or str(uuid4())
        token = REQUEST_ID_CTX_KEY.set(rid)
        try:
            response = await call_next(request)
        finally:
            REQUEST_ID_CTX_KEY.reset(token)
        response.headers[self.header_name] = rid
        return response
