# ba# backend/routes/chat_proxy.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import httpx

from backend.config.settings import settings
from backend.utils.logging import get_logger

log = get_logger(__name__)

# ⚠️ OJO: NO uses /api aquí si luego montas este router con prefix="/api"
# Así evitas terminar con /api/api/...
router = APIRouter(prefix="/chat-proxy", tags=["Chat Proxy"])

# ─────────────────────────────────────────────────────────
# Config Rasa: base tomado de settings + overrides por ENV
# ─────────────────────────────────────────────────────────

# Base: lo que ya usas en todo el backend
base_url = (os.getenv("RASA_BASE_URL") or settings.RASA_BASE_URL).rstrip("/")

# URL REST final (se puede sobreescribir si quieres)
RASA_REST_URL = (
    os.getenv("RASA_REST_URL")
    or f"{base_url}/webhooks/rest/webhook"
).rstrip("/")

CHAT_REQUIRE_AUTH = (os.getenv("CHAT_REQUIRE_AUTH", "false") or "false").lower() == "true"
RASA_TIMEOUT_MS = int(os.getenv("RASA_TIMEOUT_MS", "8000"))

# Endpoints alternativos para health en Rasa
RASA_STATUS_URLS = [
    os.getenv("RASA_STATUS_URL") or f"{base_url}/status",
    os.getenv("RASA_HEALTH_URL") or f"{base_url}/health",
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
# Health del chat-proxy (no envía mensaje al bot)
# GET /chat-proxy/health  → si montas con prefix="/api" => /api/chat-proxy/health
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

    log.error("chat_proxy health: Rasa no responde. last_err=%s", last_err)
    raise HTTPException(status_code=503, detail=last_err or "Rasa no responde")


# ─────────────────────────────────────────────────────────
# Proxy principal: POST /chat-proxy
# Si lo montas con prefix="/api" → POST /api/chat-proxy
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
            log.exception("Error conectando a Rasa en %s: %s", RASA_REST_URL, e)
            raise HTTPException(status_code=502, detail=f"Error conectando a Rasa: {e}")

    if not (200 <= r.status_code < 300):
        detail = r.text or "error al enviar mensaje"
        log.error("Rasa respondió status=%s body=%s", r.status_code, detail)
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
