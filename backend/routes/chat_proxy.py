# backend/routes/chat_proxy.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/api/chat", tags=["chat"])

# ─────────────────────────────────────────────────────────
# Config desde ENV (con defaults seguros para Docker compose)
# ─────────────────────────────────────────────────────────
RASA_REST_URL = (
    os.getenv("RASA_REST_URL")
    or os.getenv("RASA_HTTP")
    or "http://rasa:5005/webhooks/rest/webhook"
).rstrip("/")

CHAT_REQUIRE_AUTH = (os.getenv("CHAT_REQUIRE_AUTH", "false") or "false").lower() == "true"
RASA_TIMEOUT_MS = int(os.getenv("RASA_TIMEOUT_MS", "8000"))

# Endpoints alternativos para health en Rasa
RASA_STATUS_URLS = [
    os.getenv("RASA_STATUS_URL") or f"{RASA_REST_URL.replace('/webhooks/rest/webhook','')}/status",
    os.getenv("RASA_HEALTH_URL") or f"{RASA_REST_URL.replace('/webhooks/rest/webhook','')}/health",
]

# ─────────────────────────────────────────────────────────
# Modelos de entrada
# ─────────────────────────────────────────────────────────
class ChatIn(BaseModel):
    text: Optional[str] = None
    message: Optional[str] = None
    sender: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────────────────
# Util: obtener usuario desde middleware de auth (si existe)
# ─────────────────────────────────────────────────────────
def _get_user_from_request(request: Request) -> Optional[Dict[str, Any]]:
    # Tu AuthMiddleware ya popula request.state.user cuando hay JWT/cookie válidos.
    return getattr(request.state, "user", None)


# ─────────────────────────────────────────────────────────
# Health del chat (no envía mensaje al bot)
# GET /api/chat/health
# ─────────────────────────────────────────────────────────
@router.get("/health")
async def chat_health() -> Dict[str, Any]:
    last_err: Optional[str] = None
    timeout = httpx.Timeout(RASA_TIMEOUT_MS / 1000.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for url in RASA_STATUS_URLS:
            try:
                r = await client.get(url)
                if 200 <= r.status_code < 500:
                    return {"ok": True, "target": url, "status": r.status_code}
            except Exception as e:
                last_err = str(e)
    raise HTTPException(status_code=503, detail=last_err or "Rasa no responde")


# ─────────────────────────────────────────────────────────
# Proxy principal: POST /api/chat
# Acepta { text | message, sender, metadata } y reenvía a Rasa
# ─────────────────────────────────────────────────────────
@router.post("")
async def chat_send(body: ChatIn, request: Request) -> List[Dict[str, Any]]:
    # 🔒 Si decidiste exigir auth para chatear (opcional por ENV)
    if CHAT_REQUIRE_AUTH:
        user = _get_user_from_request(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")

    text = (body.text or body.message or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Mensaje vacío")

    payload = {
        "sender": (body.sender or _get_or_create_sender_id(request)),
        "message": text,
        "metadata": body.metadata or {},
    }

    timeout = httpx.Timeout(RASA_TIMEOUT_MS / 1000.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            r = await client.post(RASA_REST_URL, json=payload)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error conectando a Rasa: {e}")

    if not (200 <= r.status_code < 300):
        detail = r.text or "error al enviar mensaje"
        raise HTTPException(status_code=r.status_code, detail=detail)

    try:
        data = r.json()
    except Exception:
        data = []

    # Rasa responde array de eventos [{ "text": "..."} ...]
    return data if isinstance(data, list) else []


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────
SENDER_HEADER = "X-Chat-Sender"

def _get_or_create_sender_id(request: Request) -> str:
    # 1) Intentar cabecera (si algún proxy/frontend la envía)
    sid = request.headers.get(SENDER_HEADER)
    if sid:
        return sid

    # 2) Intentar IP+UA para una huella simple (no PII fuerte)
    ip = (request.client.host if request.client else "0.0.0.0")
    ua = request.headers.get("user-agent", "web")
    return f"web-{abs(hash((ip, ua))) % (10**10)}"
