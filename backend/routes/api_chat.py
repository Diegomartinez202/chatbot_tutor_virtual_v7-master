# backend/routes/api_chat.py
from fastapi import APIRouter, Request
from pydantic import BaseModel
import httpx
from typing import Any, Dict, Optional

from backend.config.settings import settings
from backend.services.jwt_service import decode_token
from backend.middleware.request_id import get_request_id
from backend.utils.logging import get_logger
from backend.rate_limit import limit

log = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["api-chat"])


class ChatPayload(BaseModel):
    sender: str
    message: Optional[str] = None
    metadata: Dict[str, Any] = {}


@router.post("/chat")
@limit("60/minute")
async def chat_proxy(payload: ChatPayload, request: Request):
    auth_header = request.headers.get("Authorization")
    is_valid, claims = decode_token(auth_header)

    meta = payload.metadata or {}
    meta["auth"] = {"hasToken": bool(is_valid), "claims": claims if is_valid else {}}
    payload.metadata = meta

    body = payload.model_dump()
    rid = get_request_id()
    headers = {"X-Request-ID": rid, "Content-Type": "application/json"}

    rasa_url = settings.rasa_url
    if not rasa_url:
        raise RuntimeError("RASA_URL no está configurado en settings.")

    log.debug(f"Proxy → Rasa: {rasa_url} (rid={rid})")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(rasa_url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    log.info(f"Rasa responded (count={len(data)}, rid={rid})")
    return data