# backend/routes/logs_v2.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from typing import List
import re

from backend.dependencies.auth import require_role, get_current_user
from backend.services.log_service import (
    listar_archivos_log,
    obtener_contenido_log,
    exportar_logs_csv_stream,
    contar_mensajes_no_leidos,
    marcar_mensajes_como_leidos,
    get_logs,
    log_access,
    get_export_logs,
    get_export_stats_by_day,
)

from backend.models.log_model import LogModel
from backend.rate_limit import limit  # no-op si SlowAPI no está activo

# 👇 prefijo v2 (sustentación)
router = APIRouter(prefix="/api/admin2", tags=["Logs v2"])

# 📄 1. Listar logs (misma lógica/roles/servicios)
@router.get("/admin/logs", response_model=List[LogModel], summary="📄 Listar logs desde MongoDB (v2)")
@limit("30/minute")
def listar_logs_v2(request: Request, current_user=Depends(require_role(["admin", "soporte"]))):
    logs = get_logs()
    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint=str(request.url.path),
        method=request.method,
        status=200 if logs else 204,
        ip=getattr(request.state, "ip", None),
        user_agent=getattr(request.state, "user_agent", None),
    )
    return logs

# ⬇️ 2. Descargar archivo de log local
@router.get("/admin/logs/{filename}", summary="⬇️ Descargar archivo de log local (v2)")
@limit("10/minute")
def descargar_log_v2(filename: str, request: Request, current_user=Depends(require_role(["admin", "soporte"]))):
    if not re.match(r"^train_.*\.log$", filename):
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

    file_path = obtener_contenido_log(filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint=str(request.url.path),
        method=request.method,
        status=200,
        ip=getattr(request.state, "ip", None),
        user_agent=getattr(request.state, "user_agent", None),
    )
    return FileResponse(file_path, media_type="text/plain", filename=filename)

# 📤 3. Exportar logs a CSV
@router.get("/admin/logs/export", summary="📤 Exportar logs a CSV (v2)", response_class=StreamingResponse)
@limit("10/minute")
def exportar_logs_csv_v2(request: Request, current_user=Depends(require_role(["admin", "soporte"]))):
    output = exportar_logs_csv_stream()
    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint=str(request.url.path),
        method=request.method,
        status=200,
        ip=getattr(request.state, "ip", None),
        user_agent=getattr(request.state, "user_agent", None),
        tipo="exportacion_csv",
    )
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=logs_exportados.csv"},
    )

# 📊 4. Exportaciones por día (para gráfico)
@router.get("/admin/logs/exports", summary="📊 Estadísticas de exportaciones por día (v2)")
@limit("30/minute")
def estadisticas_exportaciones_v2(request: Request, current_user=Depends(require_role(["admin", "soporte"]))):
    data = get_export_stats_by_day()
    return JSONResponse(content=data)

# 📄 5. Lista detallada de exportaciones
@router.get("/admin/logs/exports/list", summary="📄 Lista detallada de exportaciones CSV (v2)")
@limit("30/minute")
def listar_exportaciones_v2(request: Request, current_user=Depends(require_role(["admin", "soporte"]))):
    data = get_export_logs()
    return JSONResponse(content=data)

# 🔴 6. Contar mensajes no leídos (por usuario)
@router.get("/logs/unread_count", summary="🔴 No leídos (v2)")
@limit("60/minute")
def get_unread_count_v2(user_id: str = Query(...), current_user=Depends(get_current_user)):
    return {"unread": contar_mensajes_no_leidos(user_id)}

# ✅ 7. Marcar mensajes como leídos
@router.post("/logs/mark_read", summary="✅ Marcar mensajes como leídos (v2)")
@limit("20/minute")
def marcar_mensajes_leidos_v2(user_id: str = Query(...), current_user=Depends(get_current_user)):
    return {"updated_count": marcar_mensajes_como_leidos(user_id)}

# 📉 8. Fallidos (fallbacks) recientes
@router.get("/admin/intents/failures", summary="📉 Intentos fallidos (v2)")
@limit("30/minute")
def intentos_fallidos_v2(request: Request, current_user=Depends(require_role(["admin", "soporte"]))):
    from backend.services.log_service import get_fallback_logs
    return get_fallback_logs()

# 📊 9. Top fallidos
@router.get("/admin/intents/failures/top", summary="📊 Top intents fallidos (v2)")
@limit("30/minute")
def top_fallbacks_v2(request: Request, current_user=Depends(require_role(["admin", "soporte"]))):
    from backend.services.log_service import get_top_failed_intents
    return get_top_failed_intents()