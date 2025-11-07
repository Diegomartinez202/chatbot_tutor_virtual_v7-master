"""
Módulo de conexión y utilidades para autosave de conversaciones o snapshots
📚 Proyecto: Chatbot Tutor Virtual Zajuna
"""

import os
import logging
from datetime import datetime
from pymongo import MongoClient, errors

# =========================================================
# 🔧 Configuración dinámica (segura y compatible con Docker)
# =========================================================

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")  # 👉 'mongo' es el nombre del servicio en docker-compose
DB_NAME = os.getenv("MONGO_DB", "chatbot_tutor_virtual")
COLLECTION = os.getenv("MONGO_AUTOSAVE_COLLECTION", "autosaves")

# =========================================================
# 🧠 Inicialización del cliente
# =========================================================

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    autosave_collection = db[COLLECTION]
    # Verifica conexión
    client.admin.command("ping")
    print(f"✅ Conectado correctamente a MongoDB: {MONGO_URI}")
except errors.ConnectionFailure as e:
    logging.error(f"❌ Error de conexión con MongoDB: {e}")
    client = None
    db = None
    autosave_collection = None

# =========================================================
# 💾 Función: guardar snapshot o autosave
# =========================================================
def guardar_autosave(sender_id: str, data: dict):
    """
    Guarda un snapshot automático de una conversación en MongoDB.

    Args:
        sender_id (str): ID único de la conversación (por ejemplo, tracker.sender_id)
        data (dict): Datos del estado o contenido a guardar.
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
def obtener_autosaves(limit: int = 5):
    """
    Recupera los últimos autosaves registrados.
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
def limpiar_autosaves(dias: int = 30):
    """
    Elimina autosaves más antiguos que el número de días especificado.
    """
    if not autosave_collection:
        logging.warning("⚠️ No hay conexión activa con MongoDB.")
        return 0

    try:
        limite = datetime.utcnow().timestamp() - dias * 86400
        result = autosave_collection.delete_many({"timestamp": {"$lt": datetime.utcfromtimestamp(limite)}})
        logging.info(f"🧹 Eliminados {result.deleted_count} autosaves antiguos.")
        return result.deleted_count
    except Exception as e:
        logging.error(f"❌ Error limpiando autosaves: {e}")
        return 0
