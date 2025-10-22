# backend/routes/chat.py
from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Optional, Any, Dict, List

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from backend.config.settings import settings
from backend.middleware.request_id import get_request_id
from backend.services.jwt_service import decode_token
from backend.db.mongodb import get_logs_collection
from backend.services.chat_service import process_user_message
from backend.utils.logging import get_logger

# ✅ Rate limiting por endpoint (compat: builtin/slowapi/fastapi-limiter)
from backend.rate_limit import limit               # decorador seguro (no rompe si está desactivado)
from backend.ext.rate_limit import limiter         # dependencia opcional (no-op si no hay Redis)

# Mantén este nombre: main.py hace `from backend.routes.chat import chat_router`
chat_router = APIRouter(prefix="/chat", tags=["Chat"])
log = get_logger(__name__)


# ==== Modelos ====
class ChatRequest(BaseModel):
    # Compat: el frontend envía "sender"; internamente usamos sender_id
    sender_id: str = Field(default="anonimo", alias="sender", description="ID de sesión o usuario")
    message: str
    metadata: Optional[Dict[str, Any]] = None
    mode: Optional[str] = "anonymous"

    # 🆕 Pydantic v2: reemplaza Config por model_config
    # - validate_by_name: permite poblar por nombre de campo cuando hay alias
    # - extra="allow": acepta claves extra sin romper (como antes)
    model_config = ConfigDict(
        validate_by_name=True,
        extra="allow",
    )


# ==== Endpoints auxiliares ====
@chat_router.get("/health", summary="Healthcheck de chat")
async def chat_health():
    return {"ok": True}


@chat_router.get("/debug", summary="Inspección de request (solo DEBUG)")
async def chat_debug(request: Request):
    if not settings.debug:
        # No revelar en producción
        raise HTTPException(status_code=404, detail="Not Found")

    rid = get_request_id()
    ip = request.client.host if request.client else "-"
    ua = request.headers.get("user-agent", "-")

    return {
        "ok": True,
        "debug": True,
        "request_id": rid,
        "ip": ip,
        "user_agent": ua,
        "headers_sample": {
            "x-request-id": request.headers.get("x-request-id"),
            "authorization": "present" if request.headers.get("authorization") else "absent",
            "referer": request.headers.get("referer"),
        },
    }


# ==== Endpoint principal ====
@chat_router.post(
    "",
    summary="Enviar mensaje al chatbot y registrar en MongoDB",
    # FastAPI-Limiter (si está habilitado): 60 req / 60 s
    dependencies=limiter(times=60, seconds=60),
)
@limit("60/minute")  # Builtin/SlowAPI (si está habilitado): 60 req / min
async def send_message_to_bot(data: ChatRequest, request: Request):
    # Metadata de red (del middleware) con fallback
    ip = getattr(request.state, "ip", None) or request.headers.get("x-forwarded-for") \
         or (request.client.host if request.client else "unknown")
    user_agent = getattr(request.state, "user_agent", None) or request.headers.get("user-agent", "")
    rid = get_request_id()

    # 1) Validar JWT y construir metadata.auth (backend = fuente de verdad)
    auth_header = request.headers.get("Authorization")
    is_valid, claims = decode_token(auth_header)

    enriched_meta: Dict[str, Any] = dict(data.metadata or {})
    enriched_meta["auth"] = {
        "hasToken": bool(is_valid),
        "claims": claims if is_valid else {},
    }

    # Añadir referer si no viene (auditoría)
    if "url" not in enriched_meta and "referer" in request.headers:
        enriched_meta["url"] = request.headers.get("referer")

    # 2) Enviar a Rasa (propagando metadata) con medición de latencia
    t0 = perf_counter()
    try:
        try:
            bot_responses: List[Dict[str, Any]] = await process_user_message(
                data.message, data.sender_id, metadata=enriched_meta  # type: ignore
            )
        except TypeError:
            # Compat con firmas antiguas sin "metadata"
            bot_responses = await process_user_message(data.message, data.sender_id)
    except Exception as e:
        log.error(f"Error al comunicar con Rasa: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Error al comunicar con Rasa: {str(e)}")
    latency_ms = int((perf_counter() - t0) * 1000)

    # 3) Intent defensivo (si viene adjunto en la 1ª respuesta)
    intent = None
    try:
        if bot_responses and isinstance(bot_responses[0], dict):
            intent = (
                bot_responses[0].get("intent", {}).get("name")
                or bot_responses[0].get("metadata", {}).get("intent")
            )
    except Exception:
        intent = None

    # 4) Log en Mongo (best-effort)
    log_doc = {
        "request_id": rid,
        "sender_id": data.sender_id,
        "user_message": data.message,
        "bot_response": [
            r.get("text") if isinstance(r, dict) else str(r)
            for r in (bot_responses or [])
        ],
        "intent": intent,
        "timestamp": datetime.utcnow(),
        "ip": ip,
        "user_agent": user_agent,
        "origen": "widget" if data.sender_id == "anonimo" else "autenticado",
        "metadata": enriched_meta,
        "latency_ms": latency_ms,
    }
    try:
        get_logs_collection().insert_one(log_doc)
    except Exception as e:
        # No bloquear el flujo por fallo de log
        log.warning(f"No se pudo guardar el log en Mongo: {e}")

    # 5) Responder en formato Rasa (lista de mensajes)
    return bot_responses