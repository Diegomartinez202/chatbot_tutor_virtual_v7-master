# =====================================================
# 🧩 backend/services/stt.py  (REEMPLAZO COMPLETO)
# =====================================================
from __future__ import annotations

import os
import httpx
from typing import Any, Dict, Optional

from backend.config.settings import settings
from backend.middleware.request_id import get_request_id

# ---------------------------
# Helper para obtener URL STT
# ---------------------------
def _get_stt_url() -> str | None:
    """
    Obtiene la URL del servicio STT desde settings o env.
    Prioridad: settings.stt_url > STT_URL (env)
    """
    url = getattr(settings, "stt_url", None) or os.getenv("STT_URL")
    return url.strip() if isinstance(url, str) and url.strip() else None

# ---------------------------
# Stub sencillo (modo sin STT)
# ---------------------------
def transcribe_stub(_: bytes, *, lang: str = "es", provider: str = "none") -> Optional[str]:
    """
    Si no hay proveedor real configurado, devuelve None (sin transcripción).
    """
    if provider == "none":
        return None
    # aquí podrías rutear a otros backends (whisper/gcloud) localmente
    return None

# ---------------------------
# Cliente STT asíncrono (tuyo)
# ---------------------------
async def transcribe_audio(data: bytes, mime: str, lang: str = "es") -> Dict[str, Any]:
    """
    Envía audio al servicio STT. Si no hay URL configurada, retorna valores por defecto.
    Propaga 'X-Request-ID' para trazabilidad.
    """
    stt_url = _get_stt_url()
    if not stt_url:
        return {"text": "", "lang": lang, "model": "none", "confidence": 0}

    files = {"audio": ("audio.webm", data, mime)}
    form = {"lang": lang}
    headers = {"X-Request-ID": get_request_id() or ""}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(stt_url, files=files, data=form, headers=headers)
            r.raise_for_status()
            j = r.json()
            return {
                "text": j.get("text", "") or "",
                "lang": j.get("language", lang) or lang,
                "model": j.get("model", "whisper") or "whisper",
                "confidence": j.get("confidence", 0.9),
            }
    except Exception:
        # No romper el flujo si el STT falla
        return {"text": "", "lang": lang, "model": "none", "confidence": 0}
