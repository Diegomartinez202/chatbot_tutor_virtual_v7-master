# =====================================================
# 🧩 backend/services/rasa_client.py
# =====================================================
from __future__ import annotations

from typing import Any, Dict, Optional
import httpx

from backend.config.settings import settings
from backend.middleware.request_id import get_request_id


def _get_rasa_url() -> str:
    """
    Obtiene la URL del webhook REST de Rasa desde settings de forma segura.
    """
    url = getattr(settings, "rasa_url", None) or getattr(settings, "RASA_REST_URL", None)
    if not url:
        # fallback legacy (solo si se configuró por env en algún sitio)
        import os
        url = os.getenv("RASA_REST_URL", "").strip()
    if not url:
        # valor por defecto (mismo que tenías antes)
        url = "http://localhost:5005/webhooks/rest/webhook"
    return str(url)


async def send_to_rasa(sender: str, message: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Envía el mensaje al webhook REST de Rasa y retorna la respuesta JSON.
    Propaga X-Request-ID para trazabilidad end-to-end.
    """
    rasa_url = _get_rasa_url()
    headers = {
        "Content-Type": "application/json",
        "X-Request-ID": get_request_id() or "",
    }
    payload: Dict[str, Any] = {
        "sender": sender,
        "message": message,
        "metadata": metadata or {},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(rasa_url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()