# backend/middleware/permissions_policy.py
from __future__ import annotations

from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import Response

_PRESETS = {
    "strict":  "microphone=(), camera=(), geolocation=(), payment=()",
    "relaxed": "microphone=(self), camera=(self)",
    "open":    "microphone=*, camera=*",
}

def add_permissions_policy(
    app: FastAPI,
    *,
    policy: Optional[str] = None,
    preset: str = "strict",
    add_legacy_feature_policy: bool = False,   # ⬅️ FALSE por defecto
) -> None:
    value = (policy or _PRESETS.get(preset) or _PRESETS["strict"]).strip()

    @app.middleware("http")
    async def _permissions_policy_mw(request: Request, call_next):
        resp: Response = await call_next(request)
        if "Permissions-Policy" not in resp.headers:
            resp.headers["Permissions-Policy"] = value
        # ❌ no enviamos Feature-Policy
        return resp
