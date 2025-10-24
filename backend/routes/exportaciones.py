# backend/routes/exportaciones.py
from __future__ import annotations

from datetime import datetime
from io import StringIO
import csv

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import StreamingResponse

from backend.dependencies.auth import require_role
from backend.services import stats_service
from backend.services.log_service import exportar_logs_csv_filtrado, log_access
from backend.db.mongodb import get_database
from backend.utils.file_utils import save_csv_to_s3_and_get_url

# ✅ Rate limiting por endpoint (no-op si SlowAPI está deshabilitado)
from backend.rate_limit import limit

router = APIRouter()

# usar DB a través del helper
db = get_database()


@router.get(
    "/admin/exportaciones",
    summary="📤 Exportar logs en formato CSV (tipo: descarga)",
    response_class=StreamingResponse
)
@limit("10/minute")
def exportar_logs_csv(
    request: Request,
    desde: str = Query(None, description="Fecha inicio YYYY-MM-DD"),
    hasta: str = Query(None, description="Fecha fin YYYY-MM-DD"),
    user=Depends(require_role(["admin", "soporte"]))
):
    try:
        desde_dt = datetime.strptime(desde, "%Y-%m-%d") if desde else None
        hasta_dt = datetime.strptime(hasta, "%Y-%m-%d") if hasta else None
    except ValueError:
        return {"error": "Formato de fecha inválido. Usa YYYY-MM-DD"}

    log_access(
        user_id=user["_id"],
        email=user["email"],
        rol=user["rol"],
        endpoint="/admin/exportaciones",
        method=request.method,
        status=200,
        ip=getattr(request.state, "ip", None),
        user_agent=getattr(request.state, "user_agent", None),
        tipo="descarga"
    )

    csv_bytes, archivo_url = exportar_logs_csv_filtrado(desde_dt, hasta_dt)

    db["exportaciones"].insert_one({
        "usuario": user["email"],
        "tipo": "logs",
        "fecha": datetime.utcnow(),
        "archivo": archivo_url
    })

    headers = {
        "Content-Disposition": f"attachment; filename={archivo_url.split('/')[-1]}"
    }
    return StreamingResponse(csv_bytes, media_type="text/csv", headers=headers)


@router.get(
    "/admin/exportaciones/lista",
    summary="📄 Lista de exportaciones registradas"
)
@limit("30/minute")
def listar_exportaciones(
    desde: str = Query(None),
    hasta: str = Query(None),
    tipo: str = Query(None),
    usuario: str = Query(None),
    limit: int = Query(50),
    user=Depends(require_role(["admin", "soporte"]))
):
    query = {}
    if desde:
        try:
            desde_dt = datetime.strptime(desde, "%Y-%m-%d")
            query["fecha"] = {"$gte": desde_dt}
        except Exception:
            return {"error": "Fecha desde inválida"}
    if hasta:
        try:
            hasta_dt = datetime.strptime(hasta, "%Y-%m-%d")
            query.setdefault("fecha", {})
            query["fecha"]["$lte"] = hasta_dt
        except Exception:
            return {"error": "Fecha hasta inválida"}
    if tipo:
        query["tipo"] = tipo
    if usuario:
        query["usuario"] = {"$regex": usuario, "$options": "i"}

    exportaciones = list(db["exportaciones"].find(query).sort("fecha", -1).limit(limit))
    for e in exportaciones:
        e["_id"] = str(e["_id"])
        e["fecha"] = e.get("fecha", datetime.utcnow()).isoformat()
    return exportaciones


@router.get("/admin/exportaciones/stats", summary="📊 Exportar estadísticas del chatbot (CSV)")
@limit("6/minute")
async def exportar_estadisticas_csv(
    request: Request,
    desde: str = Query(None),
    hasta: str = Query(None),
    user=Depends(require_role(["admin", "soporte"]))
):
    total_logs = await stats_service.obtener_total_logs(desde, hasta)
    total_exportaciones_csv = await stats_service.obtener_total_exportaciones_csv(desde, hasta)
    intents = await stats_service.obtener_intents_mas_usados(desde=desde, hasta=hasta)
    total_users = await stats_service.obtener_total_usuarios()
    last_users = await stats_service.obtener_ultimos_usuarios()
    usuarios_por_rol = await stats_service.obtener_usuarios_por_rol()
    logs_por_dia = await stats_service.obtener_logs_por_dia(desde, hasta)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Métrica", "Valor"])
    writer.writerow(["Total de logs", total_logs])
    writer.writerow(["Total exportaciones CSV", total_exportaciones_csv])
    writer.writerow(["Total usuarios", total_users])

    for r in usuarios_por_rol:
        writer.writerow([f"Usuarios rol: {r['rol']}", r["total"]])

    for i in intents:
        writer.writerow([f"Intent: {i['intent']}", i["total"]])

    for l in logs_por_dia:
        writer.writerow([f"Logs en {l['fecha']}", l["total"]])

    writer.writerow(["Últimos usuarios", "email (rol)"])
    for u in last_users:
        writer.writerow(["", f"{u['email']} ({u['rol']})"])

    csv_text = output.getvalue()
    csv_bytes, archivo_url = save_csv_to_s3_and_get_url(csv_text, filename_prefix="estadisticas")

    db["exportaciones"].insert_one({
        "usuario": user["email"],
        "tipo": "estadisticas",
        "archivo": archivo_url,
        "fecha": datetime.utcnow()
    })

    log_access(
        user_id=user["_id"],
        email=user["email"],
        rol=user["rol"],
        endpoint=str(request.url.path),
        method=request.method,
        status=200,
        ip=getattr(request.state, "ip", None),
        user_agent=getattr(request.state, "user_agent", None)
    )

    return StreamingResponse(
        csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=estadisticas.csv"}
    )