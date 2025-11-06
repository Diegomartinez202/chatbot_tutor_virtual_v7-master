from __future__ import annotations
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/status", include_in_schema=False)
async def status():
    return {"ok": True, "service": "backend", "status": "ready"}

@router.get("/live", include_in_schema=False)
async def live():
    return {"ok": True}

@router.get("/ready", include_in_schema=False)
async def ready():
    # aquí podrías chequear conexiones reales (mongo, redis, rasa)
    return {"ok": True}
