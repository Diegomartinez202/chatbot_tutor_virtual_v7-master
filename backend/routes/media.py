# app/routers/media.py
from __future__ import annotations

import os
from typing import Optional
from bson import ObjectId

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import StreamingResponse, Response

import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# ✅ Rate limiting por endpoint (no-op si SlowAPI está deshabilitado)
from backend.rate_limit import limit

router = APIRouter(prefix="/api/media", tags=["media"])

# ─────────────────────────────────────────────────────────────
# Config
#   - Compat: lee MONGO_URL/MONGODB_URL y MONGO_DB/MONGODB_DB
#   - Habilita GridFS sólo si GRIDFS_ENABLED=true
# ─────────────────────────────────────────────────────────────
MONGO_URL = os.getenv("MONGO_URL", os.getenv("MONGODB_URL", "mongodb://localhost:27017")).strip()
MONGO_DB = os.getenv("MONGO_DB", os.getenv("MONGODB_DB", "chatbot_admin")).strip()
GRIDFS_ENABLED = (os.getenv("GRIDFS_ENABLED", "false").lower() == "true")

# ─────────────────────────────────────────────────────────────
# Mongo / GridFS
# ─────────────────────────────────────────────────────────────
_client: AsyncIOMotorClient = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
_db = _client[MONGO_DB]
_fs_bucket = None
if GRIDFS_ENABLED:
    try:
        _fs_bucket = motor.motor_asyncio.AsyncIOMotorGridFSBucket(_db, bucket_name="uploads")
    except Exception:
        _fs_bucket = None


def _guess_mime(meta_mime: Optional[str], filename: Optional[str]) -> str:
    """Best-effort para derivar el MIME si no viene en metadata."""
    if meta_mime:
        return meta_mime
    if filename:
        fn = filename.lower()
        if fn.endswith(".webm"):
            return "audio/webm"
        if fn.endswith(".ogg"):
            return "audio/ogg"
        if fn.endswith(".mp3"):
            return "audio/mpeg"
        if fn.endswith(".wav"):
            return "audio/wav"
        if fn.endswith(".m4a") or fn.endswith(".mp4"):
            return "audio/mp4"
    return "application/octet-stream"


async def _open_gridout_or_404(media_id: str):
    """Abre un stream de GridFS o lanza 404 en caso de error/config inválida."""
    if not GRIDFS_ENABLED or _fs_bucket is None:
        raise HTTPException(status_code=404, detail="Media store deshabilitado.")
    if not ObjectId.is_valid(media_id):
        raise HTTPException(status_code=404, detail="ID inválido.")
    try:
        gridout = await _fs_bucket.open_download_stream(ObjectId(media_id))
        return gridout
    except Exception:
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")


async def _stream_range(gridout, start: int, end: int, chunk_size: int = 1024 * 256):
    """Generador async para enviar el rango solicitado en chunks."""
    remaining = (end - start) + 1
    await gridout.seek(start)
    while remaining > 0:
        chunk = await gridout.read(min(chunk_size, remaining))
        if not chunk:
            break
        yield chunk
        remaining -= len(chunk)


@router.get("/{media_id}")
@limit("30/minute")  # streaming/descarga de binarios
async def get_media(
    media_id: str,
    request: Request,
    download: bool = Query(default=False, description="Forzar descarga ('attachment')"),
):
    """
    Sirve archivos desde GridFS con soporte de HTTP Range (streaming).
    - `download=true` fuerza Content-Disposition 'attachment'; por defecto 'inline'.
    """
    gridout = await _open_gridout_or_404(media_id)

    total = gridout.length
    filename = getattr(gridout, "filename", None)
    meta = getattr(gridout, "metadata", {}) or {}
    mime = _guess_mime(meta.get("mime"), filename)

    # Soporte Range: bytes=start-end
    range_header = request.headers.get("range") or request.headers.get("Range")
    status_code = 200
    headers = {
        "Accept-Ranges": "bytes",
    }

    if range_header and range_header.startswith("bytes="):
        try:
            range_spec = range_header.split("=", 1)[1]
            start_s, end_s = range_spec.split("-")
            start = int(start_s) if start_s else 0
            end = int(end_s) if end_s else total - 1
            if start < 0 or end >= total or start > end:
                return Response(status_code=416)  # Range Not Satisfiable
            status_code = 206
            headers["Content-Range"] = f"bytes {start}-{end}/{total}"
            headers["Content-Length"] = str((end - start) + 1)
            body = _stream_range(gridout, start, end)
        except Exception:
            # Si falla el parse del rango, devolvemos el archivo completo
            headers["Content-Length"] = str(total)
            body = _stream_range(gridout, 0, total - 1)
    else:
        # Sin Range → archivo completo
        headers["Content-Length"] = str(total)
        body = _stream_range(gridout, 0, total - 1)

    disp_name = filename or f"{media_id}.bin"
    disposition = "attachment" if download else "inline"
    headers["Content-Disposition"] = f'{disposition}; filename="{disp_name}"'

    return StreamingResponse(body, status_code=status_code, media_type=mime, headers=headers)


@router.head("/{media_id}")
@limit("60/minute")  # HEAD es liviano (preflight)
async def head_media(
    media_id: str,
    download: bool = Query(default=False, description="Forzar descarga ('attachment')"),
):
    """
    HEAD para obtener metadatos sin transferir el binario.
    Útil para preflight de players (obtiene Content-Length/MIME).
    """
    gridout = await _open_gridout_or_404(media_id)

    total = gridout.length
    filename = getattr(gridout, "filename", None)
    meta = getattr(gridout, "metadata", {}) or {}
    mime = _guess_mime(meta.get("mime"), filename)

    disp_name = filename or f"{media_id}.bin"
    disposition = "attachment" if download else "inline"

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(total),
        "Content-Type": mime,
        "Content-Disposition": f'{disposition}; filename="{disp_name}"',
    }
    return Response(status_code=200, headers=headers)