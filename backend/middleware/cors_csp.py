# backend/middleware/cors_csp.py
from __future__ import annotations

from typing import List
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import settings


def _merge_origins(a: List[str] | None, b: List[str] | None) -> List[str]:
    arr = []
    for lst in (a or []), (b or []):
        for it in lst:
            s = (it or "").strip()
            if s and s not in arr:
                arr.append(s)
    return arr


def add_cors_and_csp(app: FastAPI) -> None:
    """
    Añade CORS + CSP en base a settings.
    - CORS usa union(ALLOWED_ORIGINS, EMBED_ALLOWED_ORIGINS)
    - CSP usa union(FRAME_ANCESTORS, EMBED_ALLOWED_ORIGINS) en frame-ancestors
    - No elimina tu lógica actual; puedes usarlo en lugar del bloque inline.
    """
    # ---- CORS ----
    cors_origins = _merge_origins(settings.allowed_origins, settings.embed_allowed_origins)
    if not cors_origins:
        cors_origins = ["*"]  # dev-friendly, puedes endurecer en prod

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
        max_age=86400,
    )

    # ---- CSP ----
    @app.middleware("http")
    async def _csp_headers(request: Request, call_next):
        resp = await call_next(request)

        # CSP construido desde settings (ya unificado)
        csp_value = settings.build_csp()
        resp.headers["Content-Security-Policy"] = csp_value

        # Hardening extra no intrusivo
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-XSS-Protection"] = "0"
        # Permissions-Policy (ajústala a tu gusto)
        resp.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )
        return resp
