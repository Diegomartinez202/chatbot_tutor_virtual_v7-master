# backend/routes/logs.py
# ASCII-only comments to avoid encoding issues in some containers.

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

from backend.services.log_service import (
    # file utilities
    listar_archivos_log,
    obtener_contenido_log,
    # csv exports
    exportar_logs_csv_stream,
    exportar_logs_csv_filtrado,
    registrar_exportacion_csv,
    # unread helpers
    contar_mensajes_no_leidos,
    marcar_mensajes_como_leidos,
    # logs and stats
    get_logs,
    get_export_stats,
    get_export_logs,
    get_fallback_logs,
    get_top_failed_intents,
)

router = APIRouter(prefix="/api/logs", tags=["Logs"])


# ----------------------------
# Local log files (if any)
# ----------------------------
@router.get("/files")
def list_log_files():
    """
    List local .log files under settings.log_dir (if available).
    """
    return listar_archivos_log()


@router.get("/files/{filename}")
def get_log_file(filename: str):
    """
    Return the path to a local log file if it exists; 404 otherwise.
    """
    path = obtener_contenido_log(filename)
    if not path:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    # Return content path or small hint. If you want to stream the file,
    # you can open it and return StreamingResponse, but we keep current behavior.
    return {"path": path}


# ----------------------------
# CSV exports
# ----------------------------
@router.get("/export.csv")
def export_logs_csv():
    """
    Stream a simple CSV of logs (columns: user_id, message, timestamp, sender, intent).
    """
    sio = exportar_logs_csv_stream()
    headers = {"Content-Disposition": 'attachment; filename="logs.csv"'}
    return StreamingResponse(sio, media_type="text/csv", headers=headers)


@router.get("/export/filtered.csv")
def export_logs_csv_filtered(
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
):
    """
    Generate a filtered CSV (string) for downloads or S3; returns CSV directly.
    Date format expected: ISO8601 (e.g., 2025-01-31T00:00:00).
    """
    dt_desde: Optional[datetime] = datetime.fromisoformat(desde) if desde else None
    dt_hasta: Optional[datetime] = datetime.fromisoformat(hasta) if hasta else None

    csv_text = exportar_logs_csv_filtrado(dt_desde, dt_hasta)
    headers = {"Content-Disposition": 'attachment; filename="logs_filtered.csv"'}
    return Response(content=csv_text, media_type="text/csv", headers=headers)


@router.post("/export/register")
def register_csv_export(
    user_id: str,
    email: str,
    rol: str,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
):
    """
    Register a CSV export (persists a 'descarga' log) and uploads to S3 via save_csv_to_s3_and_get_url.
    Returns a presigned URL.
    """
    dt_desde: Optional[datetime] = datetime.fromisoformat(desde) if desde else None
    dt_hasta: Optional[datetime] = datetime.fromisoformat(hasta) if hasta else None

    # Build a minimal user dict expected by registrar_exportacion_csv
    user = {
        "_id": user_id,
        "id": user_id,  # keep both to be safe
        "email": email,
        "rol": rol,
        "ip": ip,
        "user_agent": user_agent,
    }
    url = registrar_exportacion_csv(user, dt_desde, dt_hasta)
    if not url:
        raise HTTPException(status_code=500, detail="No se pudo registrar la exportacion")
    return {"url": url}


# ----------------------------
# Unread helpers
# ----------------------------
@router.get("/unread/{user_id}")
def unread_count(user_id: str):
    """
    Return unread count per user_id.
    """
    return {"unread": contar_mensajes_no_leidos(user_id)}


@router.post("/mark-read/{user_id}")
def mark_read(user_id: str):
    """
    Mark pending messages as read for user_id.
    """
    modified = marcar_mensajes_como_leidos(user_id)
    return {"updated": modified}


# ----------------------------
# Logs and stats
# ----------------------------
@router.get("")
def list_logs(limit: int = 100):
    """
    Return latest 'acceso' logs.
    """
    return get_logs(limit=limit)


@router.get("/exports")
def list_export_logs(limit: int = 50):
    """
    Return latest 'descarga' logs.
    """
    return get_export_logs(limit=limit)


@router.get("/stats/by-day")
def export_stats_by_day():
    """
    Return per-day export stats. Aligns with service name `get_export_stats`.
    """
    return get_export_stats()


@router.get("/fallbacks")
def list_fallback_logs(limit: int = 100):
    """
    Return latest NLU fallback logs.
    """
    return get_fallback_logs(limit=limit)


@router.get("/top-failed")
def top_failed_intents():
    """
    Return top 5 failed intents (fallback-like).
    """
    return get_top_failed_intents()
