# app/routers/admin_failed.py
from __future__ import annotations

from datetime import date
import csv
import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

# ✅ Rate limiting por endpoint (no-op si SlowAPI no está habilitado)
from backend.rate_limit import limit

router = APIRouter(prefix="/admin/intentos-fallidos", tags=["admin-intentos-fallidos"])


@router.get("/top")
@limit("30/minute")  # consultas de ranking (ligero)
def top_failed(desde: date | None = None, hasta: date | None = None, limit: int = 10):
    # Demo/placeholder. Mantén tu fuente real si existe.
    data = [
        {"intent": "fallback", "count": 42},
        {"intent": "soporte_contacto", "count": 18},
    ]
    return data[:limit]


@router.get("/logs")
@limit("30/minute")  # listado/paginado de logs (moderado)
def failed_logs(
    desde: date | None = None,
    hasta: date | None = None,
    intent: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    # Demo/placeholder. Mantén tu fuente real si existe.
    items = [
        {
            "_id": "1",
            "timestamp": "2025-08-08T12:00:00Z",
            "email": "a@b.c",
            "message": "hola",
            "intent": intent or "fallback",
        }
    ] * 5
    return {"items": items, "total": 5, "page": page, "page_size": page_size}


@router.get("/export")
@limit("10/minute")  # exportación CSV (más costoso)
def export_failed(desde: date | None = None, hasta: date | None = None, intent: str | None = None):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "email", "message", "intent"])
    writer.writerow(["2025-08-08T12:00:00Z", "a@b.c", "hola", intent or "fallback"])
    output.seek(0)

    # Construcción robusta del nombre de archivo
    desde_str = (str(desde) if desde else "").strip()
    hasta_str = (str(hasta) if hasta else "").strip()
    filename_base = f"intentos_fallidos_{desde_str}_{hasta_str}".strip("_").replace("__", "_")
    filename = filename_base or "intentos_fallidos"

    headers = {"Content-Disposition": f'attachment; filename="{filename}.csv"'}
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )