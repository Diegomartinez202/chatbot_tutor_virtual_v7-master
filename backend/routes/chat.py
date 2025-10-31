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
from backend.rate_limit import limit
from backend.ext.rate_limit import limiter

router = APIRouter()
chat_router = APIRouter(prefix="/chat", tags=["Chat"])
log = get_logger(__name__)


# ==== Modelos ====
class ChatRequest(BaseModel):
    sender_id: str = Field(default="anonimo", alias="sender", description="ID de sesión o usuario")
    message: str
    metadata: Optional[Dict[str, Any]] = None
    mode: Optional[str] = "anonymous"

    model_config = ConfigDict(
        validate_by_name=True,
        extra="allow",
    )


# ==== Endpoints auxiliares ====
@chat_router.get("/health", summary="Healthcheck de chat")
async def chat_health():
    """Verifica que el servicio de chat esté operativo."""
    return {"ok": True, "rasa_url": settings.rasa_url}


@chat_router.get("/debug", summary="Inspección de request (solo DEBUG)")
async def chat_debug(request: Request):
    if not settings.debug:
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
    dependencies=limiter(times=60, seconds=60),
)
@limit("60/minute")
async def send_message_to_bot(data: ChatRequest, request: Request):
    ip = (
        getattr(request.state, "ip", None)
        or request.headers.get("x-forwarded-for")
        or (request.client.host if request.client else "unknown")
    )
    user_agent = getattr(request.state, "user_agent", None) or request.headers.get("user-agent", "")
    rid = get_request_id()

    # Validar JWT
    auth_header = request.headers.get("Authorization")
    is_valid, claims = decode_token(auth_header)

    enriched_meta: Dict[str, Any] = dict(data.metadata or {})
    enriched_meta["auth"] = {"hasToken": bool(is_valid), "claims": claims if is_valid else {}}

    if "url" not in enriched_meta and "referer" in request.headers:
        enriched_meta["url"] = request.headers.get("referer")

    # Comunicación con Rasa
    t0 = perf_counter()
    try:
        # ✅ Endurecido: no pasamos kwargs extras a process_user_message
        bot_responses: List[Dict[str, Any]] = await process_user_message(
            message=data.message,
            sender_id=data.sender_id,
            metadata=enriched_meta,
        )
    except Exception as e:
        log.error(f"❌ Error al comunicar con Rasa ({settings.rasa_url}): {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Error al comunicar con Rasa: {str(e)}")
    latency_ms = int((perf_counter() - t0) * 1000)

    # Intent detectado
    intent = None
    try:
        if bot_responses and isinstance(bot_responses[0], dict):
            intent = (
                bot_responses[0].get("intent", {}).get("name")
                or bot_responses[0].get("metadata", {}).get("intent")
            )
    except Exception:
        pass

    # Guardar log
    log_doc = {
        "request_id": rid,
        "sender_id": data.sender_id,
        "user_message": data.message,
        "bot_response": [r.get("text") if isinstance(r, dict) else str(r) for r in (bot_responses or [])],
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
        log.warning(f"No se pudo guardar el log en Mongo: {e}")

    return bot_responses


# ==== Demo ====
@router.post("/demo", summary="Demo sin conexión Rasa")
async def chat_demo(data: ChatRequest):
    """Respuesta local de prueba sin conexión a Rasa."""
    user_message = data.message.lower().strip()
    if "hola" in user_message:
        bot_responses = [{"text": "👋 ¡Hola! Soy el bot tutor virtual de Zajuna. ¿En qué puedo ayudarte hoy?"}]
    elif "gracias" in user_message:
        bot_responses = [{"text": "😊 ¡De nada! Estoy aquí para ayudarte."}]
    elif "adiós" in user_message or "chao" in user_message:
        bot_responses = [{"text": "👋 ¡Hasta pronto! Que tengas un gran día."}]
    else:
        bot_responses = [{"text": "🤖 Esta es una respuesta de prueba del bot Zajuna."}]
    return bot_responses


# ==== Proxy hacia Rasa ====
@router.post("/rasa/rest/webhook", summary="Proxy REST → Rasa")
async def rasa_rest_proxy(payload: dict):
    """
    Reenvía mensajes al servidor Rasa (puerto 5005 en docker).
    Adjunta metadata mínima si no viene desde el frontend.
    """
    payload.setdefault("metadata", {}).setdefault("ui", {"proxied": True})

    rasa_url = "http://rasa:5005/webhooks/rest/webhook"
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            r = await client.post(rasa_url, json=payload)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log.error(f"❌ Error proxying to Rasa: {e}")
            return {"error": "No se pudo contactar con el servidor Rasa"}

__all__ = ["router"]