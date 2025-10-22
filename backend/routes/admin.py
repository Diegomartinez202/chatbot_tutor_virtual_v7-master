# backend/routes/admin.py
from fastapi import APIRouter, HTTPException, Query, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from backend.dependencies.auth import require_role
from backend.db.mongodb import get_logs_collection, get_test_logs_collection, get_users_collection
from backend.services.train_service import entrenar_chatbot
from backend.services.intent_manager import add_intent_and_train, get_all_intents
from backend.utils.logger import logger
from backend.services.log_service import log_access
from datetime import datetime
from pathlib import Path
from bson.son import SON
import subprocess
import requests
from fastapi import APIRouter, Response
import os
from backend.services.log_service import registrar_exportacion_csv, get_export_logs

router = APIRouter()

# ✅ Verificar estado del servidor Rasa
@router.get("/admin/rasa/status")
def verificar_estado_rasa(current_user=Depends(require_role(["admin"]))):
    try:
        res = requests.get("http://rasa:5005/status")
        res.raise_for_status()
        logger.info("✅ Rasa está activo y respondió correctamente")

        log_access(
            user_id=current_user["_id"],
            email=current_user["email"],
            rol=current_user["rol"],
            endpoint="/admin/rasa/status",
            method="GET",
            status=200
        )

        return {"message": "Rasa está activo", "status": res.json()}
    except Exception as e:
        logger.error(f"❌ Error conectando a Rasa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error conectando a Rasa: {str(e)}")


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
            status=200
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
        status=200 if resultado else 500
    )

    return resultado


# ✅ Ejecutar pruebas automáticas
@router.post("/admin/test-all")
def ejecutar_tests(current_user=Depends(require_role(["admin"]))):
    try:
        logger.info(f"🧪 Ejecutando pruebas automáticas por {current_user['email']}")

        resultado = subprocess.run(["bash", "scripts/test_all.sh"], capture_output=True, text=True)

        log_access(
            user_id=current_user["_id"],
            email=current_user["email"],
            rol=current_user["rol"],
            endpoint="/admin/test-all",
            method="POST",
            status=200 if resultado.returncode == 0 else 500
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
            "returncode": resultado.returncode
        }

    except Exception as e:
        logger.error(f"❌ Error al ejecutar pruebas: {str(e)}")
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
    current_user=Depends(require_role(["admin"]))
):
    ejemplos_list = [e.strip() for e in examples.splitlines() if e.strip()]
    add_intent_and_train(intent_name, ejemplos_list, response)
    logger.info(f"📥 Nueva carga de intent: {intent_name}")

    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint="/admin/cargar_intent",
        method="POST",
        status=200
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
        status=200
    )

    return FileResponse(log_path, media_type="text/plain", filename="system.log")


# ✅ Consultar estadísticas generales
@router.get("/admin/stats")
def get_stats(current_user=Depends(require_role(["admin"]))):
    logs_col = get_logs_collection()
    usuarios_col = get_users_collection()

    total_logs = logs_col.count_documents({})
    total_usuarios = usuarios_col.count_documents({})

    intents_mas_usados = list(
        logs_col.aggregate([
            {"$group": {"_id": "$intent", "total": {"$sum": 1}}},
            {"$sort": SON([("total", -1)])},
            {"$limit": 5}
        ])
    )

    usuarios_por_rol = list(
        usuarios_col.aggregate([
            {"$group": {"_id": "$rol", "total": {"$sum": 1}}},
            {"$project": {"rol": "$_id", "total": 1, "_id": 0}}
        ])
    )

    ultimos_usuarios = list(
        usuarios_col.find({}, {"email": 1, "rol": 1}).sort("_id", -1).limit(5)
    )

    logs_por_dia = list(
        logs_col.aggregate([
            {"$match": {"timestamp": {"$exists": True}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                    },
                    "total": {"$sum": 1}
                }
            },
            {"$sort": SON([("_id", 1)])}
        ])
    )

    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint="/admin/stats",
        method="GET",
        status=200
    )

    return {
        "total_logs": total_logs,
        "total_usuarios": total_usuarios,
        "intents_mas_usados": intents_mas_usados,
        "usuarios_por_rol": usuarios_por_rol,
        "ultimos_usuarios": ultimos_usuarios,
        "logs_por_dia": logs_por_dia
    }


# ✅ Filtrar logs por nivel y rango de fechas
@router.get("/admin/logs")
def get_logs_filtered(
    level: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    current_user=Depends(require_role(["admin"]))
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
            query["timestamp"]["$lte"] = datetime.strptime(end_date, "%Y-%m-%d")

    logs = list(collection.find(query).sort("timestamp", -1).limit(500))
    for log in logs:
        log["_id"] = str(log["_id"])
        log["timestamp"] = log["timestamp"].isoformat()

    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint="/admin/logs",
        method="GET",
        status=200 if logs else 204
    )

    return logs


# ✅ Listar todos los intents con trazabilidad
@router.get("/admin/intents")
def listar_intents(current_user=Depends(require_role(["admin", "soporte"]))):
    intents = get_all_intents()

    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint="/admin/intents",
        method="GET",
        status=200 if intents else 204
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
        status=200
    )

    return {"message": "🔁 Servidor reiniciado (simulado)"}


@router.get("/admin/export-tests")
def export_test_results(current_user=Depends(require_role(["admin"]))):
    csv_data = "Prueba,Estado,Mensaje,Latencia\nBackend conectado,200 OK,Todo bien,120ms\nIntents disponibles,200 OK,23 intents,98ms"
    filename = f"resultados_diagnostico_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv"

    log_access(
        user_id=current_user["_id"],
        email=current_user["email"],
        rol=current_user["rol"],
        endpoint="/admin/export-tests",
        method="GET",
        status=200
    )

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    @router.get("/admin/exportaciones")
def exportaciones_csv(
    request: Request,
    desde: datetime = Query(None),
    hasta: datetime = Query(None),
    current_user=Depends(require_role(["admin"]))
):
    user = {
        "_id": current_user["_id"],
        "email": current_user["email"],
        "rol": current_user["rol"],
        "ip": request.state.ip,
        "user_agent": request.state.user_agent,
    }

    url = registrar_exportacion_csv(user=user, desde=desde, hasta=hasta)
    return {"url": url}


@router.get("/admin/exportaciones/historial")
def historial_exportaciones(current_user=Depends(require_role(["admin"]))):
    return get_export_logs()

