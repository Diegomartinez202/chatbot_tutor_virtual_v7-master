# backend/routes/admin.py
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import subprocess
from typing import Optional

import httpx
from bson.son import SON
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Depends,
    Form,
    Request,
    Response,
)
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse

from backend.dependencies.auth import require_role
from backend.db.mongodb import (
    get_logs_collection,
    get_test_logs_collection,
    get_users_collection,
)
from backend.services.train_service import entrenar_chatbot
from backend.services.intent_manager import (
    guardar_intent,
    entrenar_rasa,
    obtener_intents,
)
from backend.utils.logger import logger
from backend.services.log_service import (
    log_access,
    registrar_exportacion_csv,
    get_export_logs,
)
from backend.config.settings import settings
from backend.middleware.request_id import get_request_id

router = APIRouter()


# ─────────────────────────────────────────────────────────
# Helpers URL Rasa (evita hosts fijos)
# ─────────────────────────────────────────────────────────
def _rasa_base_from_settings() -> Optional[str]:
    """
    Devuelve la base de Rasa sin el sufijo del webhook si vino completo.
    Prioriza settings.rasa_url / RASA_REST_URL; como fallback usa envs genéricos.
    """
    url = getattr(settings, "rasa_url", None) or getattr(settings, "RASA_REST_URL", None)
    if not url:
        import os as _os
        url = _os.getenv("RASA_REST_URL") or _os.getenv("RASA_HTTP") or ""
    url = (url or "").strip()
    if not url:
        return None
    # quitar /webhooks/rest/webhook si viene completo
    if url.endswith("/webhooks/rest/webhook"):
        url = url[: -len("/webhooks/rest/webhook")]
    return url.rstrip("/")


def _rasa_status_url() -> Optional[str]:
    base = _rasa_base_from_settings()
    if not base:
        return None
    return f"{base}/status"


# ✅ Verificar estado del servidor Rasa (sin host fijo)
@router.get("/admin/rasa/status")
async def verificar_estado_rasa(current_user=Depends(require_role(["admin"]))):
    url = _rasa_status_url()
    if not url:
        raise HTTPException(500, detail="RASA_URL no está configurado correctamente")

    headers = {"X-Request-ID": get_request_id() or "-"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url, headers=headers)
            res.raise_for_status()
            data = res.json()

        logger.info("✅ Rasa respondió /status ok")

        log_access(
            user_id=current_user["_id"],
            email=current_user["email"],
            rol=current_user["rol"],
            endpoint="/admin/rasa/status",
            method="GET",
            status=200,
        )
        return {"message": "Rasa está activo", "status": data}

    except Exception as e:
        logger.error(f"❌ Error conectando a Rasa en {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Error conectando a Rasa: {e}")


# ✅ Entrenar el bot manualmente
@router.get("/admin/train")
def dry_run_train(dry_run: bool = False, current_user=Depends(require_role(["admin"]))):
    if dry_run:
        logger.info("🧪 Simulación de entrenamiento realizada con éxito")
        log_access(
            user_id=current_user["_id"],
            email=current_user["email"],
            rol=current_user["rol"],
            endpoint="/admin/train",
            method="GET",
            status=200,
        )
        return {"message": "Simulación de entrenamiento realizada con éxito"}

    logger.info(f"🏋️ Entrenamiento manual del bot iniciado por {current_user['email']}")
    resultado = entrenar_chatbot()

    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint="/admin/train",
        method="GET",
        status=200 if (resultado and resultado.get("status") == "ok") else 500,
    )
    return resultado



# ✅ NUEVO ENDPOINT OPCIONAL: obtener modelo más reciente registrado
@router.get("/admin/last-model")
def obtener_ultimo_modelo(current_user=Depends(require_role(["admin"]))):
    """
    Devuelve el último modelo entrenado de Rasa registrado en MongoDB,
    incluyendo su nombre, timestamp y estado.
    """
    try:
        from pymongo import MongoClient
        mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017/tutor_virtual")
        client = MongoClient(mongo_uri)
        db = client.get_default_database() or client["rasa"]
        models_col = db["trained_models"]

        last_model = models_col.find_one(sort=[("timestamp", -1)])
        if not last_model:
            return {"message": "Aún no hay modelos registrados."}
        logger.info(
            f"📦 Último modelo consultado: {last_model.get('model_name')} en {last_model.get('timestamp')}"
        )
        return {
            "model_name": last_model.get("model_name"),
            "timestamp": last_model.get("timestamp"),
            "status": last_model.get("status", "ok"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando modelo: {e}")


# ✅ Ejecutar pruebas automáticas
@router.post("/admin/test-all")
def ejecutar_tests(current_user=Depends(require_role(["admin"]))):
    try:
        logger.info(f"🧪 Ejecutando pruebas automáticas por {current_user['email']}")
        resultado = subprocess.run(
            ["bash", "scripts/test_all.sh"], capture_output=True, text=True
        )

        log_access(
            user_id=current_user["_id"],
            email=current_user["email"],
            rol=current_user["rol"],
            endpoint="/admin/test-all",
            method="POST",
            status=200 if resultado.returncode == 0 else 500,
        )

        log_entry = {
            "usuario": current_user["email"],
            "rol": current_user.get("rol", "desconocido"),
            "fecha": datetime.utcnow(),
            "stdout": resultado.stdout,
            "stderr": resultado.stderr,
            "returncode": resultado.returncode,
        }
        get_test_logs_collection().insert_one(log_entry)

        return {
            "message": "Pruebas ejecutadas y logueadas",
            "stdout": resultado.stdout,
            "stderr": resultado.stderr,
            "returncode": resultado.returncode,
        }
    except Exception as e:
        logger.error(f"❌ Error al ejecutar pruebas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ✅ Formulario web de carga de intents
@router.get("/admin/form", response_class=HTMLResponse)
def admin_form():
    html_path = Path("backend/static/admin_form.html")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# ✅ Cargar un nuevo intent desde formulario
@router.post("/admin/cargar_intent", response_class=HTMLResponse)
def cargar_intent_form(
    intent_name: str = Form(...),
    examples: str = Form(...),
    response: str = Form(...),
    current_user=Depends(require_role(["admin"])),
):
    ejemplos_list = [e.strip() for e in examples.splitlines() if e.strip()]
    guardar_intent(
        {"intent": intent_name, "examples": ejemplos_list, "responses": [response]}
    )
    entrenar_rasa()

    logger.info(f"📥 Nueva carga de intent: {intent_name}")
    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint="/admin/cargar_intent",
        method="POST",
        status=200,
    )
    return RedirectResponse(url="/admin/form", status_code=303)


# ✅ Descargar archivo de logs del sistema
@router.get("/admin/logs-file")
def obtener_logs_de_sistema(current_user=Depends(require_role(["admin"]))):
    logger.info(f"📂 {current_user['email']} accedió a system.log")
    log_path = "logs/system.log"
    if not Path(log_path).exists():
        raise HTTPException(status_code=404, detail="Archivo de log no encontrado")

    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint="/admin/logs-file",
        method="GET",
        status=200,
    )
    return FileResponse(log_path, media_type="text/plain", filename="system.log")


# ✅ Consultar estadísticas generales (centralizado en stats_service)
@router.get("/admin/stats")
async def get_stats(
    desde: Optional[str] = Query(None, description="YYYY-MM-DD"),
    hasta: Optional[str] = Query(None, description="YYYY-MM-DD"),
    current_user=Depends(require_role(["admin"])),
):
    from backend.services import stats_service as stats  # import local para evitar ciclos

    total_logs = await stats.obtener_total_logs(desde=desde, hasta=hasta)
    total_usuarios = await stats.obtener_total_usuarios()
    intents_mas_usados = await stats.obtener_intents_mas_usados(limit=5, desde=desde, hasta=hasta)
    usuarios_por_rol = await stats.obtener_usuarios_por_rol()
    ultimos_usuarios = await stats.obtener_ultimos_usuarios(limit=5)
    logs_por_dia = await stats.obtener_logs_por_dia(desde=desde, hasta=hasta)

    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint="/admin/stats",
        method="GET",
        status=200,
    )
    return {
        "total_logs": total_logs,
        "total_usuarios": total_usuarios,
        "intents_mas_usados": intents_mas_usados,
        "usuarios_por_rol": usuarios_por_rol,
        "ultimos_usuarios": ultimos_usuarios,
        "logs_por_dia": logs_por_dia,
    }


# ✅ Filtrar logs por nivel y rango de fechas
@router.get("/admin/logs")
def get_logs_filtered(
    level: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    current_user=Depends(require_role(["admin"])),
):
    collection = get_logs_collection()
    query = {}

    if level:
        query["level"] = level.upper()

    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            # incluir fin del día
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query["timestamp"]["$lte"] = end_dt
    logs = list(collection.find(query).sort("timestamp", -1).limit(500))
    for log in logs:
        log["_id"] = str(log["_id"])
        if isinstance(log.get("timestamp"), datetime):
            log["timestamp"] = log["timestamp"].isoformat()

    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint="/admin/logs",
        method="GET",
        status=200 if logs else 204,
    )
    return logs


# ✅ Listar todos los intents
@router.get("/admin/intents")
def listar_intents(current_user=Depends(require_role(["admin", "soporte"]))):
    intents = obtener_intents()
    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint="/admin/intents",
        method="GET",
        status=200 if intents else 204,
    )
    return intents


@router.post("/admin/restart")
def restart_server(current_user=Depends(require_role(["admin"]))):
    os.system("touch restart_signal.txt")
    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint="/admin/restart",
        method="POST",
        status=200,
    )
    return {"message": "🔁 Servidor reiniciado (simulado)"}


@router.get("/admin/export-tests")
def export_test_results(current_user=Depends(require_role(["admin"]))):
    csv_data = (
        "Prueba,Estado,Mensaje,Latencia\n"
        "Backend conectado,200 OK,Todo bien,120ms\n"
        "Intents disponibles,200 OK,23 intents,98ms"
    )
    filename = f"resultados_diagnostico_{datetime.now().strftime('%Y-%m-%d')}.csv"

    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint="/admin/export-tests",
        method="GET",
        status=200,
    )
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ✅ Exportaciones CSV → S3 + registro
@router.get("/admin/exportaciones")
def exportaciones_csv(
    request: Request,
    desde: datetime = Query(None),
    hasta: datetime = Query(None),
    current_user=Depends(require_role(["admin"])),
):
    user = {
        "_id": current_user["_id"],
        "email": current_user["email"],
        "rol": current_user["rol"],
        "ip": getattr(request.state, "ip", None),
        "user_agent": getattr(request.state, "user_agent", None),
    }
    url = registrar_exportacion_csv(user=user, desde=desde, hasta=hasta)
    return {"url": url}


@router.get("/admin/exportaciones/historial")
def historial_exportaciones(current_user=Depends(require_role(["admin"]))):
    return get_export_logs()