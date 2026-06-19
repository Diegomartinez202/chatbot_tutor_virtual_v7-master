from __future__ import annotations
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from backend.utils.logging import get_logger

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])
log = get_logger(__name__)

@router.post("")
async def collect(req: Request):
    try:
        payload = await req.json()
    except Exception:
        payload = {}
    # Guarda a logs por ahora (puedes enviarlo a Mongo/Redis después)
    log.info("telemetry_event", extra={"payload": payload})
    return JSONResponse({"ok": True})
