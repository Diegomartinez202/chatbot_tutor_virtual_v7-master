import os
import httpx

STT_URL = os.getenv("STT_URL")  # ej: http://localhost:9000/transcribe

async def transcribe_audio(data: bytes, mime: str, lang: str = "es"):
    if not STT_URL:
        return {"text": "", "lang": lang, "model": "none", "confidence": 0}
    files = {"audio": ("audio.webm", data, mime)}
    data_form = {"lang": lang}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(STT_URL, files=files, data=data_form)
        r.raise_for_status()
        j = r.json()
        return {
            "text": j.get("text", ""),
            "lang": j.get("language", lang),
            "model": j.get("model", "whisper"),
            "confidence": j.get("confidence", 0.9),
        }
