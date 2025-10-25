# backend/services/chat_service.py
from __future__ import annotations

from typing import List, Dict, Any, Optional
import httpx

from backend.config.settings import settings
from backend.middleware.request_id import get_request_id
from backend.utils.logging import get_logger

log = get_logger(__name__)


def _normalize_url(u: Optional[str]) -> str:
    """
    Normaliza una URL básica (quita espacios, evita None).
    NO agrega rutas ni modifica la semántica que ya tienes configurada.
    """
    if not u:
        return ""
    return str(u).strip()


async def process_user_message(
    message: str,
    sender_id: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Envía el mensaje al webhook REST de Rasa y devuelve la lista de respuestas.
    Propaga X-Request-ID para correlación end-to-end.
    Mantiene la lógica de negocio original.
    """
    # 1) Validaciones básicas
    rasa_url_raw = getattr(settings, "rasa_url", None)
    rasa_url = _normalize_url(rasa_url_raw)
    if not rasa_url:
        raise RuntimeError("RASA_URL no está configurado en settings.")

    if not isinstance(message, str) or message.strip() == "":
        raise ValueError("El mensaje debe ser un string no vacío.")
    if not isinstance(sender_id, str) or sender_id.strip() == "":
        raise ValueError("sender_id debe ser un string no vacío.")

    # 2) Construcción del payload (sin cambiar el formato original)
    payload: Dict[str, Any] = {
        "sender": sender_id,
        "message": message,
    }
    if metadata is not None:
        payload["metadata"] = metadata

    # 3) Encabezados con correlación + agente
    rid = get_request_id() or "-"
    headers = {
        "Content-Type": "application/json",
        "X-Request-ID": rid,  # 🔗 correlación
        "User-Agent": "chatbot-backend/1.0 (+rasa-proxy)",
    }

    log.debug(f"[chat_service] → Rasa POST {rasa_url} (rid={rid})")

    # 4) Llamada HTTP con timeouts razonables
    #    (no altera comportamiento: sigue haciendo 1 petición)
    try:
        timeout = httpx.Timeout(30.0)  # connect/read/write/pool total
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
            resp = await client.post(rasa_url, json=payload, headers=headers)
            resp.raise_for_status()
            try:
                data = resp.json()
            except ValueError as je:
                # Respuesta sin JSON válido
                raise ValueError(f"Respuesta de Rasa no es JSON válido: {je}") from je
    except httpx.HTTPStatusError as he:
        # Preservamos el contexto y dejamos claro qué pasó
        log.error(
            f"[chat_service] HTTP {he.response.status_code} desde Rasa "
            f"(rid={rid}): {he.response.text[:500]}"
        )
        raise
    except httpx.RequestError as re:
        # Errores de conexión / timeout
        log.error(f"[chat_service] Error de red hacia Rasa (rid={rid}): {re}")
        raise
    except Exception as e:
        log.error(
            f"[chat_service] Error inesperado al llamar a Rasa (rid={rid}): {e}",
            exc_info=True,
        )
        raise

    # 5) Validación del formato esperado
    if not isinstance(data, list):
        raise ValueError(
            f"Respuesta de Rasa inesperada (se esperaba lista): {type(data)}"
        )

    log.debug(f"[chat_service] ← Rasa {len(data)} mensajes (rid={rid})")
    return data
