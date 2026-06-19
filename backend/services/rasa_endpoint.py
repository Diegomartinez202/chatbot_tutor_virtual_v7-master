# =====================================================
# 🧩 backend/services/rasa_endpoint.py
# =====================================================
from __future__ import annotations
import os
from backend.config.settings import settings


def rasa_rest_endpoint() -> str:
    """
    Devuelve el endpoint REST de Rasa listo para usar.
    - Si existe RASA_REST_URL => se usa tal cual
    - Si solo hay RASA_URL => se completa con /webhooks/rest/webhook
    - Fallback: http://rasa:5005/webhooks/rest/webhook
    """
    # Preferimos la propiedad inteligente ya definida en settings
    base = (getattr(settings, "rasa_rest_base", None) or "").strip()
    if not base:
        # Fallback ultra defensivo (por si settings no trae valor)
        base = os.getenv("RASA_REST_URL") or os.getenv("RASA_URL") or "http://rasa:5005"

    base = base.rstrip("/")
    if base.endswith("/webhooks/rest/webhook"):
        return base
    return f"{base}/webhooks/rest/webhook"
