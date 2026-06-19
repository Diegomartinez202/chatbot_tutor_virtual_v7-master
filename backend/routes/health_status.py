# backend/routes/health_status.py
from __future__ import annotations

from fastapi import APIRouter
from starlette import status as http_status

# Un solo router, sin prefix "/api" porque eso ya se agrega en main.py
router = APIRouter(tags=["Health"])


@router.get("/status", include_in_schema=False)
async def health_status():
    """
    Endpoint simple para verificar que el backend responde.
    """
    return {"ok": True, "service": "backend", "status": "ready"}


@router.get("/live", include_in_schema=False)
async def live():
    """
    Liveness probe: ¿el proceso está vivo?
    """
    return {"ok": True}


@router.get("/ready", include_in_schema=False)
async def ready():
    """
    Readiness probe: aquí podrías validar Mongo, Redis, Rasa, etc.
    """
    return {"ok": True}


@router.get("/health", status_code=http_status.HTTP_200_OK)
async def health_check():
    """
    Health check "oficial" para Docker, monitoreo, etc.
    """
    return {
        "status": "ok",
        "service": "zajuna-chat-backend",
        "version": "2.0.0",
    }
