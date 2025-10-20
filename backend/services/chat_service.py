# backend/services/chat_service.py
from typing import List, Dict, Any, Optional
import httpx

from backend.config.settings import settings
from backend.middleware.request_id import get_request_id
from backend.utils.logging import get_logger

log = get_logger(__name__)

async def process_user_message(
    message: str,
    sender_id: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Envía el mensaje al webhook REST de Rasa y devuelve la lista de respuestas.
    Propaga X-Request-ID para correlación end-to-end.
    """
    if not settings.rasa_url:
        raise RuntimeError("RASA_URL no está configurado en settings.")

    payload: Dict[str, Any] = {
        "sender": sender_id,
        "message": message,
    }
    if metadata is not None:
        payload["metadata"] = metadata

    headers = {
        "Content-Type": "application/json",
        "X-Request-ID": get_request_id(),  # 🔗 correlación
    }

    log.debug(f"Proxy → Rasa: {settings.rasa_url} (rid={headers['X-Request-ID']})")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(settings.rasa_url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    if not isinstance(data, list):
        raise ValueError(f"Respuesta de Rasa inesperada (se esperaba lista): {type(data)}")

    log.debug(f"Rasa ← {len(data)} mensajes (rid={headers['X-Request-ID']})")
    return data
