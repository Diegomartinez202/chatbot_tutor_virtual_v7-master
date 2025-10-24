# =====================================================
# 🧩 backend/services/stt.py
# =====================================================
from __future__ import annotations

import os
import httpx
from typing import Any, Dict

from backend.config.settings import settings
from backend.middleware.request_id import get_request_id


def _get_stt_url() -> str | None:
    """
    Obtiene la URL del servicio STT desde settings o env.
    Prioridad: settings.stt_url > STT_URL (env)
    """
    url = getattr(settings, "stt_url", None) or os.getenv("STT_URL")
    return url.strip() if isinstance(url, str) and url.strip() else None


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
