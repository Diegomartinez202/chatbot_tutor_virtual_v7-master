import os
import csv
from bson import ObjectId
from io import StringIO
from datetime import datetime
from collections import defaultdict

from backend.db.mongodb import get_logs_collection
# ❌ Evita import circular de LOG_DIR
# from backend.config.settings import LOG_DIR
from backend.config.settings import settings
from backend.utils.file_utils import save_csv_to_s3_and_get_url

# Mantener variable original para no tocar el resto del código
LOG_DIR = settings.log_dir


# 📂 Utilidades de archivos locales
def listar_archivos_log():
    try:
        archivos = [f for f in os.listdir(LOG_DIR) if f.endswith(".log")]
        return {"archivos": archivos}
    except Exception as e:
        return {"error": str(e)}


def obtener_contenido_log(filename: str):
    ruta = os.path.join(LOG_DIR, filename)
    return ruta if os.path.exists(ruta) else None


# 📤 Exportación CSV simple
def exportar_logs_csv_stream():
    logs = get_logs_collection().find()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["user_id", "message", "timestamp", "sender", "intent"])
    for log in logs:
        writer.writerow([
            log.get("user_id", ""),
            log.get("message", ""),
            log.get("timestamp", ""),
            log.get("sender", ""),
            log.get("intent", ""),
        ])
    output.seek(0)
    return output


# 🔄 No leídos
def contar_mensajes_no_leidos(user_id: str):
    return get_logs_collection().count_documents({"user_id": user_id, "leido": False})


def marcar_mensajes_como_leidos(user_id: str):
    result = get_logs_collection().update_many(
        {"user_id": user_id, "leido": False},
        {"$set": {"leido": True}}
    )
    return result.modified_count


# 📚 Logs generales
def get_logs(limit: int = 100):
    logs = list(get_logs_collection().find({"tipo": "acceso"}).sort("timestamp", -1).limit(limit))
    for log in logs:
        log["_id"] = str(log["_id"])
    return logs


# 🟦 Registrar logs manualmente
def log_access(user_id: str, email: str, rol: str, endpoint: str, method: str, status: int, ip: str = None, user_agent: str = None, tipo: str = "acceso"):
    doc = {
        "user_id": str(user_id),
        "email": email,
        "rol": rol,
        "endpoint": endpoint,
        "method": method,
        "status": status,
        "timestamp": datetime.utcnow(),
        "ip": ip,
        "user_agent": user_agent,
        "tipo": tipo
    }
    get_logs_collection().insert_one(doc)


# 🟨 Middleware automático
def log_access_middleware(endpoint: str, method: str, status: int, ip: str, user_agent: str, user: dict = None):
    doc = {
        "endpoint": endpoint,
        "method": method,
        "status": status,
        "ip": ip,
        "user_agent": user_agent,
        "tipo": "acceso",
        "timestamp": datetime.utcnow()
    }
    if user:
        doc.update({
            "user_id": str(user.get("id") or user.get("_id")),
            "email": user.get("email"),
            "rol": user.get("rol")
        })
    get_logs_collection().insert_one(doc)


# 📊 Exportaciones estadísticas
def get_export_stats():
    pipeline = [
        {"$match": {"tipo": "descarga"}},
        {"$group": {
            "_id": {
                "year": {"$year": "$timestamp"},
                "month": {"$month": "$timestamp"},
                "day": {"$dayOfMonth": "$timestamp"}
            },
            "total": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    result = list(get_logs_collection().aggregate(pipeline))
    return [{
        "date": f"{r['_id']['year']}-{r['_id']['month']:02}-{r['_id']['day']:02}",
        "total": r["total"]
    } for r in result]


def get_export_logs(limit: int = 50):
    logs = list(get_logs_collection().find({"tipo": "descarga"}).sort("timestamp", -1).limit(limit))
    for log in logs:
        log["_id"] = str(log["_id"])
        log["timestamp"] = log.get("timestamp", datetime.utcnow()).isoformat()
    return logs


# 📉 Fallbacks
def get_fallback_logs(limit: int = 100):
    logs = list(get_logs_collection().find({"intent": "nlu_fallback"}).sort("timestamp", -1).limit(limit))
    for log in logs:
        log["_id"] = str(log["_id"])
        log["timestamp"] = log.get("timestamp", datetime.utcnow()).isoformat()
    return logs


def get_top_failed_intents():
    pipeline = [
        {"$match": {"intent": {"$ne": None}, "intent": {"$regex": ".*fallback.*", "$options": "i"}}},
        {"$group": {"_id": "$intent", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    result = list(get_logs_collection().aggregate(pipeline))
    return [{"intent": r["_id"], "count": r["count"]} for r in result]


# ✅ FILTRADO Y SUBIDA A S3
def exportar_logs_csv_filtrado(desde: datetime = None, hasta: datetime = None):
    query = {"tipo": "descarga"}
    if desde or hasta:
        query["timestamp"] = {}
        if desde:
            query["timestamp"]["$gte"] = desde
        if hasta:
            query["timestamp"]["$lte"] = hasta

    logs = get_logs_collection().find(query).sort("timestamp", -1)

    csv_str = StringIO()
    writer = csv.writer(csv_str)
    writer.writerow(["user_id", "email", "timestamp", "endpoint", "method", "status", "ip", "user_agent"])
    for log in logs:
        writer.writerow([
            log.get("user_id", ""),
            log.get("email", ""),
            log.get("timestamp", "").isoformat() if log.get("timestamp") else "",
            log.get("endpoint", ""),
            log.get("method", ""),
            log.get("status", ""),
            log.get("ip", ""),
            log.get("user_agent", "")
        ])
    return csv_str.getvalue()


# ✅ NUEVA FUNCIÓN ÚNICA Y REUTILIZABLE
def registrar_exportacion_csv(user: dict, desde: datetime = None, hasta: datetime = None):
    csv_content = exportar_logs_csv_filtrado(desde, hasta)
    url = save_csv_to_s3_and_get_url(csv_content, filename_prefix="logs")

    log_access(
        user_id=user.get("_id") or user.get("id"),
        email=user.get("email"),
        rol=user.get("rol"),
        endpoint="/admin/exportaciones",
        method="GET",
        status=200,
        ip=user.get("ip"),
        user_agent=user.get("user_agent"),
        tipo="descarga"
    )

    return url