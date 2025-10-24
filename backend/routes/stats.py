# backend/routes/stats.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Query
from backend.dependencies.auth import require_role
from backend.services import stats_service
from backend.services.log_service import log_access
from backend.models.stats_model import EstadisticasChatbotResponse

# ✅ Rate limiting por endpoint (no-op si SlowAPI está deshabilitado)
from backend.rate_limit import limit

router = APIRouter(tags=["stats"])


@router.get(
    "/admin/stats",
    summary="📊 Obtener estadísticas del chatbot",
    response_model=EstadisticasChatbotResponse,
)
@limit("30/minute")  # consultas de métricas (moderado)
async def get_stats(
    request: Request,
    desde: str = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    hasta: str = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    user=Depends(require_role(["admin", "soporte"])),
):
    total_logs = await stats_service.obtener_total_logs(desde, hasta)
    total_exportaciones_csv = await stats_service.obtener_total_exportaciones_csv(desde, hasta)
    intents = await stats_service.obtener_intents_mas_usados(desde=desde, hasta=hasta)
    total_users = await stats_service.obtener_total_usuarios()
    last_users = await stats_service.obtener_ultimos_usuarios()
    usuarios_por_rol = await stats_service.obtener_usuarios_por_rol()
    logs_por_dia = await stats_service.obtener_logs_por_dia(desde, hasta)

    log_access(
        user_id=user["_id"],
        email=user["email"],
        rol=user["rol"],
        endpoint=str(request.url.path),
        method=request.method,
        status=200,
        ip=getattr(request.state, "ip", None),
        user_agent=getattr(request.state, "user_agent", None),
    )

    return {
        "total_logs": total_logs,
        "total_exportaciones_csv": total_exportaciones_csv,
        "intents_mas_usados": intents,
        "total_usuarios": total_users,
        "ultimos_usuarios": last_users,
        "usuarios_por_rol": usuarios_por_rol,
        "logs_por_dia": logs_por_dia,
    }
