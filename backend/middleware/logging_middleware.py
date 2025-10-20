from time import perf_counter
from typing import Callable
from starlette.types import ASGIApp, Receive, Scope, Send

class LoggingMiddleware:
    """
    Middleware ASGI minimalista para loguear método, ruta, status y duración.
    No depende de nada externo.
    """
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        method = scope.get("method")
        path = scope.get("path")
        start = perf_counter()
        status_code_container = {"status": None}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code_container["status"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            dur_ms = (perf_counter() - start) * 1000
            status = status_code_container["status"]
            print(f"[REQ] {method} {path} -> {status} ({dur_ms:.1f} ms)")
