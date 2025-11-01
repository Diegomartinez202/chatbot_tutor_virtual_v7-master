# =====================================================
# 🎙 backend/routes/voice.py  (NUEVO)
# =====================================================
from __future__ import annotations

import os
import time
from typing import Optional, Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

from bson import ObjectId
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket

from backend.services.stt import transcribe_audio, transcribe_stub

router = APIRouter(prefix="/api/voice", tags=["Voice"])

# ─────────────────────────────────────────────────────────────
# Config (alineada con app/routers/media.py)
# ─────────────────────────────────────────────────────────────
MONGO_URL = os.getenv("MONGO_URL", os.getenv("MONGODB_URL", "mongodb://localhost:27017")).strip()
MONGO_DB = os.getenv("MONGO_DB", os.getenv("MONGODB_DB", "chatbot_admin")).strip()
GRIDFS_ENABLED = (os.getenv("GRIDFS_ENABLED", "false").lower() == "true")

_client: AsyncIOMotorClient = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
_db = _client[MONGO_DB]
_fs_bucket: Optional[AsyncIOMotorGridFSBucket] = None
if GRIDFS_ENABLED:
    try:
        _fs_bucket = motor.motor_asyncio.AsyncIOMotorGridFSBucket(_db, bucket_name="uploads")
    except Exception:
        _fs_bucket = None

async def _store_audio_gridfs(data: bytes, filename: str, content_type: str, metadata: Dict[str, Any]) -> Optional[str]:
    if not GRIDFS_ENABLED or _fs_bucket is None:
        return None
    file_id = await _fs_bucket.upload_from_stream(
        filename=filename,
        source=data,
        metadata={"mime": content_type, **(metadata or {})},
        chunk_size_bytes=1024 * 255,
    )
    return str(file_id)

async def _insert_voice_log(doc: Dict[str, Any]) -> None:
    try:
        await _db["voice_logs"].insert_one(doc)
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────
@router.post("/transcribe")
async def post_transcribe(
    file: UploadFile = File(...),
    sender: Optional[str] = Form(default=None),
    lang: str = Form(default="es"),
    stt: str = Form(default="auto"),  # auto|none (auto = usa transcribe_audio si hay STT_URL)
):
    try:
        t0 = time.time()
        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="Archivo vacío")

        content_type = file.content_type or "application/octet-stream"
        meta = {"sender": sender, "lang": lang, "stt": stt, "ts": int(t0 * 1000)}

        file_id: Optional[str] = await _store_audio_gridfs(
            raw,
            filename=file.filename or f"voice-{int(t0*1000)}.webm",
            content_type=content_type,
            metadata=meta,
        )

        # STT: si stt=none -> stub; si stt=auto -> intenta STT real; si falla -> stub
        transcript = None
        if stt == "none":
            transcript = transcribe_stub(raw, lang=lang, provider="none")
        else:
            stt_res = await transcribe_audio(raw, mime=content_type, lang=lang)
            transcript = (stt_res or {}).get("text") or None
            if not transcript:
                transcript = transcribe_stub(raw, lang=lang, provider="none")

        doc = {
            "file_id": ObjectId(file_id) if (file_id and ObjectId.is_valid(file_id)) else None,
            "sender": sender,
            "lang": lang,
            "stt": stt,
            "transcript": transcript,
            "content_type": content_type,
            "created_at": int(t0 * 1000),
        }
        await _insert_voice_log(doc)

        return {
            "id": file_id,
            "transcript": transcript,
            "duration_ms": None,  # si calculas duración, setéala aquí
            "mime": content_type,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando audio: {e}")

@router.get("/{id}")
async def get_audio(id: str):
    if not GRIDFS_ENABLED or _fs_bucket is None:
        raise HTTPException(status_code=404, detail="Media store deshabilitado.")
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=404, detail="ID inválido.")

    try:
        gridout = await _fs_bucket.open_download_stream(ObjectId(id))
    except Exception:
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")

    headers = {
        "Content-Type": (gridout.metadata or {}).get("mime") or "application/octet-stream",
        "Content-Length": str(gridout.length),
        "Content-Disposition": f'inline; filename="{gridout.filename or id}"',
    }
    async def gen():
        while True:
            chunk = await gridout.read(1024 * 256)
            if not chunk:
                break
            yield chunk
    return StreamingResponse(gen(), headers=headers)
