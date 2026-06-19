from __future__ import annotations

import uuid
from typing import Optional
from backend.models.voice import VoiceMeta, VoiceSaved

COLLECTION = "voice_store"


async def save_voice_blob(db, audio_file, meta: VoiceMeta) -> VoiceSaved:
    # Lee el binario (en prod guárdalo en S3/MinIO y guarda solo la URL)
    raw = await audio_file.read()
    size = len(raw or b"")
    mime = audio_file.content_type or "application/octet-stream"

    doc = {
        "id": f"va_{uuid.uuid4().hex}",
        "owner_id": meta.sender or "anon",
        "transcript": None,            # ⬅️ aquí integrarías STT si corresponde
        "duration_ms": None,           # ⬅️ puedes estimar o calcular si conoces formato
        "mime": mime,
        # si decides guardar el binario en Mongo (no ideal), podrías usar GridFS
        # aquí guardamos *temporalmente* el binario (no recomendado en prod)
        "blob": raw,                   # ⚠️ úsalo solo en dev; en prod usa storage externo
    }

    await db[COLLECTION].insert_one(doc)
    # no regreses blob en respuestas
    doc.pop("blob", None)
    return VoiceSaved(**doc)


async def get_voice_by_id(db, voice_id: str) -> Optional[dict]:
    doc = await db[COLLECTION].find_one({"id": voice_id})
    if not doc:
        return None
    doc.pop("_id", None)
    doc.pop("blob", None)  # nunca devuelvas raw en API
    return doc
