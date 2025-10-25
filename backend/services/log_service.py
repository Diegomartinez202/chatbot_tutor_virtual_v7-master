# =====================================================
# 🧩 backend/services/log_service.py
# =====================================================
from __future__ import annotations

import os
import csv
from io import StringIO
from datetime import datetime
from typing import Optional, Dict, Any, List

from bson import ObjectId  # noqa: F401 (compat / puede usarse en otros paths)

from backend.db.mongodb import get_logs_collection
from backend.config.settings import settings
from backend.utils.file_utils import save_csv_to_s3_and_get_url

# ─────────────────────────────────────────────────────
# LOG_DIR robusto (evita FieldInfo / tipos no-str)
# ─────────────────────────────────────────────────────
def _as_str(value: Any, default: str) -> str:
    try:
        if isinstance(value, str):
            return value
        return str(value)
    except Exception:
        return default

LOG_DIR = _as_str(getattr(settings, "log_dir", "./logs"), "./logs")


# 📂 Utilidades de archivos locales
def listar_archivos_log() -> Dict[str, Any]:
    try:
        archivos = [f for f in os.listdir(LOG_DIR) if f.endswith(".log")]
        return {"archivos": archivos}
    except Exception as e:
        return {"error": str(e)}


def obtener_contenido_log(filename: str) -> Optional[str]:
    ruta = os.path.join(LOG_DIR, filename)
    return ruta if os.path.exists(ruta) else None


# 📤 Exportación CSV simple (stream en memoria)
def exportar_logs_csv_stream() -> StringIO:
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
def contar_mensajes_no_leidos(user_id: str) -> int:
    return get_logs_collection().count_documents({"user_id": user_id, "leido": False})


def marcar_mensajes_como_leidos(user_id: str) -> int:
    result = get_logs_collection().update_many(
        {"user_id": user_id, "leido": False},
        {"$set": {"leido": True}}
    )
    return result.modified_count


# 📚 Logs generales
def get_logs(limit: int = 100) -> List[Dict[str, Any]]:
    logs = list(get_logs_collection().find({"tipo": "acceso"}).sort("timestamp", -1).limit(limit))
    for log in logs:
        log["_id"] = str(log["_id"])
    return logs


# 🟦 Registrar logs manualmente
def log_access(
    user_id: str,
    email: str,
    rol: str,
    endpoint: str,
    method: str,
    status: int,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    tipo: str = "acceso",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    doc: Dict[str, Any] = {
        "user_id": str(user_id),
        "email": email,
        "rol": rol,
        "endpoint": endpoint,
        "method": method,
        "status": status,
        "timestamp": datetime.utcnow(),
        "ip": ip,
        "user_agent": user_agent,
        "tipo": tipo,
    }
    if isinstance(extra, dict):
        # No sobreescribimos claves críticas
        for k, v in extra.items():
            if k not in doc:
                doc[k] = v
    get_logs_collection().insert_one(doc)


# 🟨 Middleware automático
def log_access_middleware(
    endpoint: str,
    method: str,
    status: int,
    ip: str,
    user_agent: str,
    user: Optional[dict] = None,
) -> None:
    doc: Dict[str, Any] = {
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
            "user_id": str(user.get("id") or user.get("_id") or ""),
            "email": user.get("email", ""),
            "rol": user.get("rol", "usuario")
        })
    get_logs_collection().insert_one(doc)


# 📊 Exportaciones estadísticas
def get_export_stats() -> List[Dict[str, Any]]:
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


def get_export_logs(limit: int = 50) -> List[Dict[str, Any]]:
    logs = list(get_logs_collection().find({"tipo": "descarga"}).sort("timestamp", -1).limit(limit))
    for log in logs:
        log["_id"] = str(log["_id"])
        ts = log.get("timestamp")
        log["timestamp"] = ts.isoformat() if hasattr(ts, "isoformat") else ts
    return logs


# 📉 Fallbacks
def get_fallback_logs(limit: int = 100) -> List[Dict[str, Any]]:
    logs = list(get_logs_collection().find({"intent": "nlu_fallback"}).sort("timestamp", -1).limit(limit))
    for log in logs:
        log["_id"] = str(log["_id"])
        ts = log.get("timestamp")
        log["timestamp"] = ts.isoformat() if hasattr(ts, "isoformat") else ts
    return logs


def get_top_failed_intents() -> List[Dict[str, Any]]:
    pipeline = [
        {"$match": {"intent": {"$ne": None}, "intent": {"$regex": ".*fallback.*", "$options": "i"}}},
        {"$group": {"_id": "$intent", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    result = list(get_logs_collection().aggregate(pipeline))
    return [{"intent": r["_id"], "count": r["count"]} for r in result]


# ✅ FILTRADO Y SUBIDA A S3
def exportar_logs_csv_filtrado(desde: datetime | None = None, hasta: datetime | None = None):
    """
    Genera CSV de logs (tipo: descarga) y lo sube a S3.
    ➜ Retorna (csv_bytes, archivo_url) para usar directo con StreamingResponse.
    """
    query: Dict[str, Any] = {"tipo": "descarga"}
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
        ts = log.get("timestamp")
        writer.writerow([
            log.get("user_id", ""),
            log.get("email", ""),
            ts.isoformat() if hasattr(ts, "isoformat") else ts or "",
            log.get("endpoint", ""),
            log.get("method", ""),
            log.get("status", ""),
            log.get("ip", ""),
            log.get("user_agent", "")
        ])
    csv_text = csv_str.getvalue()

    # ⬆️ Subir y obtener (bytes, url)
    csv_bytes, archivo_url = save_csv_to_s3_and_get_url(csv_text, filename_prefix="logs")
    return csv_bytes, archivo_url


# ✅ NUEVA FUNCIÓN ÚNICA Y REUTILIZABLE (usa la de arriba)
def registrar_exportacion_csv(user: dict, desde: datetime | None = None, hasta: datetime | None = None) -> str:
    """
    Genera y sube CSV a S3 (con filtros) y registra la descarga.
    Retorna la URL del archivo.
    """
    _, url = exportar_logs_csv_filtrado(desde, hasta)

    log_access(
        user_id=user.get("_id") or user.get("id") or "",
        email=user.get("email", ""),
        rol=user.get("rol", "usuario"),
        endpoint="/admin/exportaciones",
        method="GET",
        status=200,
        ip=user.get("ip"),
        user_agent=user.get("user_agent"),
        tipo="descarga"
    )

    return url