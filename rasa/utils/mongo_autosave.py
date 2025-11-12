"""
Módulo de conexión y utilidades para autosave de conversaciones o snapshots
📚 Proyecto: Chatbot Tutor Virtual Zajuna
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# =========================================
# 🧩 Dependencias de Mongo (tolerante a fallos)
# =========================================
try:
    from pymongo import MongoClient, errors
    _PYMONGO_OK = True
except Exception as _e:
    logging.warning(f"[mongo_autosave] pymongo no disponible en import-time: {_e}")
    MongoClient = None  # type: ignore
    errors = None       # type: ignore
    _PYMONGO_OK = False

# =========================================================
# 🔧 Configuración dinámica (segura y compatible con Docker)
# =========================================================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")  # 'mongo' = nombre del servicio en docker-compose
DB_NAME = os.getenv("MONGO_DB", "chatbot_tutor_virtual")
AUTOSAVE_COLLECTION = os.getenv("MONGO_AUTOSAVE_COLLECTION", "autosaves")
SECURITY_LOGS_COLLECTION = os.getenv("MONGO_SECURITY_LOGS_COLLECTION", "security_logs")

# =========================================================
# 🧠 Inicialización del cliente (seguro)
#  - No rompe el servidor si Mongo no está accesible.
#  - Si no hay pymongo, se degrada de forma segura.
# =========================================================
client: Optional[MongoClient] = None
db = None
autosave_collection = None

if _PYMONGO_OK:
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        autosave_collection = db[AUTOSAVE_COLLECTION]
        # Verifica conexión
        client.admin.command("ping")
        print(f"✅ Conectado correctamente a MongoDB: {MONGO_URI}")
    except Exception as e:
        logging.error(f"❌ Error de conexión con MongoDB: {e}")
        client = None
        db = None
        autosave_collection = None
else:
    logging.info("ℹ️ pymongo no instalado; utilidades de Mongo quedan en modo no-op.")

# =========================================================
# 💾 Función: guardar snapshot o autosave
# =========================================================
def guardar_autosave(sender_id: str, data: dict) -> bool:
    """
    Guarda un snapshot automático de una conversación en MongoDB.

    Args:
        sender_id (str): ID único de la conversación (por ejemplo, tracker.sender_id)
        data (dict): Datos del estado o contenido a guardar.

    Returns:
        bool: True si se guardó, False si no.
    """
    if not autosave_collection:
        logging.warning("⚠️ No hay conexión activa con MongoDB. No se guardó el autosave.")
        return False

    try:
        registro = {
            "sender_id": sender_id,
            "data": data,
            "timestamp": datetime.utcnow(),
        }
        autosave_collection.insert_one(registro)
        logging.info(f"💾 Autosave guardado para {sender_id}")
        return True
    except Exception as e:
        logging.error(f"❌ Error guardando autosave para {sender_id}: {e}")
        return False

# =========================================================
# 💡 Función: obtener últimos autosaves
# =========================================================
def obtener_autosaves(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Recupera los últimos autosaves registrados.

    Args:
        limit (int): Máximo de registros a devolver.

    Returns:
        list[dict]: Lista de documentos.
    """
    if not autosave_collection:
        logging.warning("⚠️ No hay conexión activa con MongoDB.")
        return []

    try:
        resultados = list(autosave_collection.find().sort("timestamp", -1).limit(limit))
        return resultados
    except Exception as e:
        logging.error(f"❌ Error al obtener autosaves: {e}")
        return []

# =========================================================
# 🧹 Función: limpiar autosaves viejos
# =========================================================
def limpiar_autosaves(dias: int = 30) -> int:
    """
    Elimina autosaves más antiguos que el número de días especificado.

    Args:
        dias (int): Antigüedad en días.

    Returns:
        int: Cantidad eliminada.
    """
    if not autosave_collection:
        logging.warning("⚠️ No hay conexión activa con MongoDB.")
        return 0

    try:
        limite_dt = datetime.utcnow() - timedelta(days=dias)
        result = autosave_collection.delete_many({"timestamp": {"$lt": limite_dt}})
        logging.info(f"🧹 Eliminados {getattr(result, 'deleted_count', 0)} autosaves antiguos.")
        return getattr(result, "deleted_count", 0)
    except Exception as e:
        logging.error(f"❌ Error limpiando autosaves: {e}")
        return 0

# =========================================================
# 🧾 Función: log_event (segura y sin romper el server)
# =========================================================
def log_event(
    event_type: str,
    payload: Optional[Dict[str, Any]] = None,
    *,
    mongo_uri: Optional[str] = None,
    db_name: Optional[str] = None,
    collection_name: Optional[str] = None,
) -> bool:
    """
    Registra un evento simple en MongoDB. Si no hay Mongo/pymongo o falla, no rompe el servidor.

    Variables de entorno por defecto:
      • MONGO_URI
      • MONGO_DB
      • MONGO_SECURITY_LOGS_COLLECTION

    Args:
        event_type (str): Tipo o nombre del evento.
        payload (dict|None): Información adicional.
        mongo_uri, db_name, collection_name (opcionales): overrides puntuales.

    Returns:
        bool: True si se registró, False si no.
    """
    try:
        _mongo_uri = mongo_uri or os.getenv("MONGO_URI") or "mongodb://mongo:27017"
        _db = db_name or os.getenv("MONGO_DB") or "rasa"
        _col = collection_name or os.getenv("MONGO_SECURITY_LOGS_COLLECTION") or "security_logs"

        if not _PYMONGO_OK:
            # pymongo no instalado o no disponible en import-time
            logging.debug("[log_event] pymongo no disponible → no-op")
            return False

        # Import en runtime para evitar fallas en import-time si falta pymongo al construir imagen
        from pymongo import MongoClient as _RuntimeMongoClient  # type: ignore

        _client = _RuntimeMongoClient(_mongo_uri, serverSelectionTimeoutMS=1500)
        _col_ref = _client[_db][_col]
        doc = {
            "event_type": event_type,
            "payload": payload or {},
            "ts": datetime.utcnow(),
        }
        _col_ref.insert_one(doc)
        return True
    except Exception as e:
        # No romper el servidor por fallar el logging
        logging.debug(f"[log_event] No se pudo registrar evento '{event_type}': {e}")
        return False


__all__ = [
    "guardar_autosave",
    "obtener_autosaves",
    "limpiar_autosaves",
    "log_event",
]
