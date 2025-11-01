# =====================================================
# 🎙 backend/routes/voice.py  (FINAL, OPTIMIZADO)
# =====================================================
from __future__ import annotations

import os
import time
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from bson import ObjectId
from pymongo import DESCENDING
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket

# Reutilizamos tus stubs/servicios (NO se elimina lógica de negocio)
from backend.services.stt import transcribe_audio, transcribe_stub

router = APIRouter(prefix="/api/voice", tags=["Voice"])

# ─────────────────────────────────────────────────────────────
# Config (alineada con /api/media)
# ─────────────────────────────────────────────────────────────
MONGO_URL = os.getenv("MONGO_URL", os.getenv("MONGODB_URL", "mongodb://mongo:27017")).strip()
MONGO_DB = os.getenv("MONGO_DB", os.getenv("MONGODB_DB", "chatbot_admin")).strip()
GRIDFS_ENABLED = (os.getenv("GRIDFS_ENABLED", "false").lower() == "true")
GRIDFS_BUCKET = os.getenv("GRIDFS_BUCKET", "uploads").strip()

_client: AsyncIOMotorClient = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
_db = _client[MONGO_DB]

_fs_bucket: Optional[AsyncIOMotorGridFSBucket] = None
if GRIDFS_ENABLED:
    try:
        _fs_bucket = motor.motor_asyncio.AsyncIOMotorGridFSBucket(_db, bucket_name=GRIDFS_BUCKET)
    except Exception:
        _fs_bucket = None

# colección de metadatos de GridFS
_fs_files = _db[f"{GRIDFS_BUCKET}.files"]


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
async def _store_audio_gridfs(
    data: bytes,
    filename: str,
    content_type: str,
    metadata: Dict[str, Any],
) -> Optional[str]:
    """Guarda audio en GridFS con metadatos; devuelve el ObjectId en str o None si está deshabilitado."""
    if not GRIDFS_ENABLED or _fs_bucket is None:
        return None
    file_id = await _fs_bucket.upload_from_stream(
        filename=filename,
        source=data,
        metadata={"mime": content_type, **(metadata or {})},
        chunk_size_bytes=1024 * 256,
    )
    return str(file_id)


def _file_doc_to_item(doc: Dict[str, Any]) -> Dict[str, Any]:
    meta = (doc.get("metadata") or {})
    _id = str(doc["_id"])
    return {
        "id": _id,
        "filename": doc.get("filename") or meta.get("original_name") or f"voice-{_id}.webm",
        "size": int(doc.get("length") or 0),
        "mime": meta.get("mime") or "audio/webm",
        "upload_date": doc.get("uploadDate"),
        "sender": meta.get("sender"),
        "session_id": meta.get("session_id"),
        "duration": meta.get("duration"),
        "transcript": meta.get("transcript"),
        "url": f"/api/media/{_id}",                 # stream reproducible
        "download_url": f"/api/media/{_id}?download=true",
    }


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────
@router.post("/transcribe")
async def post_transcribe(
    file: UploadFile = File(...),
    sender: Optional[str] = Form(default=None),
    session_id: Optional[str] = Form(default=None),
    lang: str = Form(default="es"),
    stt: str = Form(default="auto"),  # auto | none  (auto: intenta STT_URL; none: solo guarda audio)
):
    """
    Sube audio, guarda en GridFS con metadata.kind='voice' y (opcional) lo transcribe.
    Devuelve el id de GridFS y el transcript (si aplica).
    """
    try:
        t0 = time.time()
        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="Archivo vacío")

        content_type = file.content_type or "audio/webm"
        original_name = file.filename or f"voice-{int(t0*1000)}.webm"

        # Transcripción
        transcript: Optional[str] = None
        if stt == "none":
            transcript = transcribe_stub(raw, lang=lang, provider="none")
        else:
            # intenta STT real; si no hay STT_URL, el servicio te devolverá texto vacío
            stt_res = await transcribe_audio(raw, mime=content_type, lang=lang)
            transcript = (stt_res or {}).get("text") or None
            if not transcript:
                transcript = transcribe_stub(raw, lang=lang, provider="none")

        # Metadatos coherentes con /api/voice/list
        meta = {
            "kind": "voice",
            "mime": content_type,
            "sender": sender or None,
            "session_id": session_id or None,
            "transcript": transcript or "",
            "duration": None,                 # si luego calculas duración, setéala aquí
            "original_name": original_name,
            "ts": int(t0 * 1000),
        }

        file_id = await _store_audio_gridfs(
            data=raw,
            filename=original_name,
            content_type=content_type,
            metadata=meta,
        )

        return {
            "id": file_id,                    # puede ser None si GRIDFS está off
            "transcript": transcript,
            "duration_ms": None,
            "mime": content_type,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando audio: {e}")


@router.get("/{id}")
async def get_audio(id: str):
    """
    Streaming directo desde GridFS (atajo); normalmente se recomienda /api/media/{id}.
    """
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
        "Accept-Ranges": "bytes",
    }

    async def gen():
        while True:
            chunk = await gridout.read(1024 * 256)
            if not chunk:
                break
            yield chunk

    return StreamingResponse(gen(), headers=headers)


@router.get("/list")
async def list_voice(
    page: int = Query(1, ge=1, description="Página (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Items por página"),
    sender: Optional[str] = Query(None, description="Filtrar por sender"),
    session_id: Optional[str] = Query(None, description="Filtrar por sesión"),
    q: Optional[str] = Query(None, description="Búsqueda por nombre/transcript"),
):
    """
    Lista audios guardados en GridFS (solo metadatos).
    Requiere GRIDFS_ENABLED=true. Devuelve URLs reproducibles vía /api/media/{id}.
    """
    if not GRIDFS_ENABLED:
        raise HTTPException(status_code=404, detail="GridFS deshabilitado. Define GRIDFS_ENABLED=true")

    filt: Dict[str, Any] = {"metadata.kind": "voice"}
    if sender:
        filt["metadata.sender"] = sender
    if session_id:
        filt["metadata.session_id"] = session_id
    if q:
        filt["$or"] = [
            {"filename": {"$regex": q, "$options": "i"}},
            {"metadata.original_name": {"$regex": q, "$options": "i"}},
            {"metadata.transcript": {"$regex": q, "$options": "i"}},
        ]

    skip = (page - 1) * limit
    total = await _fs_files.count_documents(filt)
    cursor = _fs_files.find(filt).sort("uploadDate", DESCENDING).skip(skip).limit(limit)

    items: List[Dict[str, Any]] = []
    async for doc in cursor:
        items.append(_file_doc_to_item(doc))

    return {"total": total, "page": page, "limit": limit, "items": items}
