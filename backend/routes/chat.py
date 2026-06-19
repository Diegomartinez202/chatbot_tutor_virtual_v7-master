# backend/routes/chat.py
from __future__ import annotations
from datetime import datetime
from time import perf_counter
from typing import Optional, Any, Dict, List
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from backend.config.settings import settings
from backend.middleware.request_id import get_request_id
from backend.services.jwt_service import decode_token
from backend.db.mongodb import get_logs_collection
from backend.services.chat_service import process_user_message
from backend.utils.logging import get_logger
from backend.rate_limit import limit
from backend.ext.rate_limit import limiter
from backend.auth.deps import get_current_user_optional, CurrentUser
from fastapi.responses import JSONResponse
import httpx
import os

router = APIRouter()
chat_router = APIRouter(prefix="/chat", tags=["Chat"])
log = get_logger(__name__)
RASA_BASE_URL = os.getenv("RASA_URL", "http://rasa:5005")
RASA_BASE_URL = settings.RASA_BASE_URL.rstrip("/")
RASA_PROXY_TIMEOUT = float(os.getenv("RASA_PROXY_TIMEOUT", "30.0"))

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

@chat_router.post(
    "",
    summary="Enviar mensaje al chatbot y registrar en MongoDB",
    dependencies=limiter(times=60, seconds=60),
)
@limit("60/minute")
async def send_message_to_bot(
    data: ChatRequest,
    request: Request,
    user: Optional[CurrentUser] = Depends(get_current_user_optional),  # 👈 NUEVO
):
    ip = (
        getattr(request.state, "ip", None)
        or request.headers.get("x-forwarded-for")
        or (request.client.host if request.client else "unknown")
    )
    user_agent = getattr(request.state, "user_agent", None) or request.headers.get("user-agent", "")
    rid = get_request_id()

    # Validar JWT (para logs / metadata)
    auth_header = request.headers.get("Authorization")
    is_valid, claims = decode_token(auth_header)

    # Metadata enriquecida
    enriched_meta: Dict[str, Any] = dict(data.metadata or {})
    enriched_meta["auth"] = {
        "hasToken": bool(is_valid),
        "claims": claims if is_valid else {},
    }

    # 🔹 info del usuario autenticado (si viene con token válido desde Zajuna)
    if user is not None:
        enriched_meta["user"] = {
            "id": user.id,
            "email": user.email,
            "mode": "estudiante",
        }
    else:
        enriched_meta["user"] = {
            "id": None,
            "email": None,
            "mode": "invitado",
        }

    if "url" not in enriched_meta and "referer" in request.headers:
        enriched_meta["url"] = request.headers.get("referer")

    # =============================
    # Comunicación con Rasa
    # =============================
    t0 = perf_counter()
    bot_responses: List[Dict[str, Any]]

    try:
        bot_responses: List[Dict[str, Any]] = await process_user_message(
            message=data.message,
            sender_id=data.sender_id,
            metadata=enriched_meta,
        )
    except Exception as e:
        log.error(f"❌ Error al comunicar con Rasa ({settings.rasa_url}): {e}", exc_info=True)

        # ⬇️ En vez de lanzar error al frontend, devolvemos un mensaje normal del bot
        bot_responses = [
            {
                "recipient_id": data.sender_id,
                "text": (
                    "En este momento el motor avanzado del chatbot o el servicio de IA está presentando "
                    "demoras ⏳.\n\n"
                    "Pero puedo seguir ayudándote con explicaciones base. "
                    "Vuelve a escribir el tema que quieres aprender, por ejemplo:\n"
                    "• Contabilidad básica\n"
                    "• Desarrollo de software\n"
                    "• Servicio al cliente\n\n"
                    "Si el problema continúa varios minutos, intenta recargar la página."
                ),
            }
        ]

    latency_ms = int((perf_counter() - t0) * 1000)

    # Intent detectado (si viene algo de Rasa)
    intent = None
    try:
        if bot_responses and isinstance(bot_responses[0], dict):
            intent = (
                bot_responses[0].get("intent", {}).get("name")
                or bot_responses[0].get("metadata", {}).get("intent")
            )
    except Exception:
        pass

    # Guardar log en Mongo
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

    # 🔚 Siempre devolvemos una lista de mensajes tipo Rasa REST, nunca un error HTTP
    return bot_responses

@chat_router.post("/demo", summary="Demo sin conexión Rasa")
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

@chat_router.get("/health", summary="Healthcheck de chat (subrouter /chat)")
async def chat_health_embed():
    """
    Verifica conectividad a Rasa usando un OPTIONS barato al webhook REST.
    Útil cuando el front llama /api/chat/health (por estar debajo de `chat_router`).
    """
    rasa_url = f"{RASA_BASE_URL}/webhooks/rest/webhook"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.options(rasa_url)
        # Rasa suele responder 200/204/405 si el endpoint vive.
        ok = 200 <= r.status_code < 500
        return {"ok": bool(ok), "rasa_url": rasa_url}
    except Exception as e:
        log.exception("chat_health_embed error: %s", e)
        return {"ok": False, "rasa_url": rasa_url, "error": str(e)}


@router.get("/chat/health", summary="Healthcheck de chat (Rasa /status)")
async def chat_health_root():
    """
    Verifica el estado del servidor Rasa consultando /status.
    Queda expuesto como /api/chat/health si montas este router con prefix="/api".
    """
    status_url = f"{RASA_BASE_URL}/status"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(status_url)
            rasa_ok = r.status_code == 200
        return {"ok": rasa_ok, "rasa_url": status_url}
    except Exception as e:
        log.exception("chat_health_root error: %s", e)
        return {"ok": False, "error": str(e), "rasa_url": status_url}


@chat_router.get(
    "/rasa/rest/webhook/health",
    summary="Healthcheck REST → Rasa (via /status)",
)
async def rasa_rest_health():
    """
    Endpoint pensado para el admin-panel / widget que busca expresamente
    /api/chat/rasa/rest/webhook/health como 'health' del canal REST.

    Internamente pregunta a Rasa /status y normaliza la respuesta.
    """
    status_url = f"{RASA_BASE_URL}/status"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(status_url)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        log.exception("rasa_rest_health error: %s", e)
        return {
            "status": "down",
            "error": str(e),
            "rasa_url": status_url,
        }

    # Normalizamos lo que recibe el frontend
    return {
        "status": "ok",
        "rasa_url": status_url,
        "rasa_version": data.get("version"),
        "available_projects": list(data.get("available_projects", {}).keys()),
    }


@chat_router.post("/rasa/rest/webhook", summary="Proxy REST → Rasa")
async def rasa_rest_proxy(payload: dict, request: Request):
    """
    Proxy transparente hacia Rasa REST.

    - Reenvía el body tal cual a Rasa (/webhooks/rest/webhook).
    - Devuelve la lista de mensajes que responde Rasa.
    - SOLO interviene cuando hay error de red, timeout o error HTTP duro,
      devolviendo un mensaje entendible para el usuario, sin detalles técnicos.
    """
    url = f"{RASA_BASE_URL}/webhooks/rest/webhook"

    # Log mínimo de depuración (sin datos sensibles)
    try:
        ua = request.headers.get("user-agent", "-")
        log.info("proxy rasa start ua=%s bytes=%s", ua, len(str(payload)))
    except Exception:
        pass

    try:
        # Usamos el timeout configurable
        async with httpx.AsyncClient(timeout=RASA_PROXY_TIMEOUT) as client:
            resp = await client.post(url, json=payload)

        # Si Rasa responde con código de error HTTP (500, 503, etc.)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail_txt = e.response.text if e.response is not None else str(e)
            status_code = e.response.status_code if e.response else 502
            log.error("rasa upstream error %s: %s", status_code, detail_txt)

            # ❗ No exponemos el error técnico al frontend
            return JSONResponse(
                status_code=200,
                content=[
                    {
                        "recipient_id": payload.get("sender", "usuario"),
                        "text": (
                            "En este momento el servidor de conversación está teniendo "
                            "dificultades para procesar tu mensaje ⏳.\n\n"
                            "Intenta de nuevo en unos instantes o usa el menú principal "
                            "(Académico, Soporte, Administrativo)."
                        ),
                    }
                ],
            )

        # Intentamos parsear JSON de la respuesta de Rasa
        try:
            data = resp.json()
        except ValueError as e:
            log.exception("proxy json error: %s", e)
            return JSONResponse(
                status_code=200,
                content=[
                    {
                        "recipient_id": payload.get("sender", "usuario"),
                        "text": (
                            "He recibido una respuesta inesperada del servidor de conversación 🤖.\n\n"
                            "Por favor intenta de nuevo o formula tu pregunta de otra forma."
                        ),
                    }
                ],
            )

        # ✅ Caso normal: devolvemos tal cual lo que responda Rasa
        if not isinstance(data, list):
            log.warning("rasa proxy non-list response: %r", data)
            # Rasa REST debería devolver lista; si no, devolvemos lista vacía
            return []

        return data

    except httpx.RequestError as e:
        # Problemas de red, DNS, timeout hacia Rasa
        log.exception("proxy network error: %s", e)
        return JSONResponse(
            status_code=200,
            content=[
                {
                    "recipient_id": payload.get("sender", "usuario"),
                    "text": (
                        "Estoy teniendo problemas de conexión con el motor del chatbot 😓.\n\n"
                        "Intenta de nuevo en unos instantes o recarga la página si el problema continúa."
                    ),
                }
            ],
        )

    except Exception as e:
        # Cualquier otro error inesperado en el backend
        log.exception("proxy fatal error: %s", e)
        return JSONResponse(
            status_code=200,
            content=[
                {
                    "recipient_id": payload.get("sender", "usuario"),
                    "text": (
                        "Se presentó un error interno al procesar tu mensaje ⚠️.\n\n"
                        "Intenta nuevamente en unos segundos. Si el problema persiste, "
                        "informa al área de soporte."
                    ),
                }
            ],
        )

@router.get("/health", summary="Healthcheck API + Rasa")
async def health():
    """
    Health global del backend + Rasa.
    Se expone como /api/health a través de nginx.
    El frontend espera JSON → devolvemos siempre JSON.
    """
    status_url = f"{RASA_BASE_URL}/status"
    rasa_ok = False
    error = None

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(status_url)
            rasa_ok = (r.status_code == 200)
    except Exception as e:
        error = str(e)
        log.exception("health: error consultando Rasa /status: %s", e)

    response = {
        "ok": bool(rasa_ok), 
        "backend_ok": True,        
        "rasa_ok": bool(rasa_ok),
        "rasa_url": status_url,
    }
    if error and not rasa_ok:
        response["error"] = error

    return response
__all__ = ["router", "chat_router"]