# backend/db/mongodb.py
from __future__ import annotations

from pymongo import MongoClient, errors
from backend.config.settings import settings  # ✅ Config centralizada

# === Configuración de conexión ===
MONGO_URI = settings.mongo_uri
MONGO_DB_NAME = settings.mongo_db_name

try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=5000,
        retryWrites=True,
    )
    client.admin.command("ping")
    print(f"✅ Conexión exitosa a MongoDB: {MONGO_URI}")

    # 🟩 Índice único en email (users)
    try:
        client[MONGO_DB_NAME]["users"].create_index("email", unique=True)
        print("✅ Índice único en 'email' creado/verificado")
    except Exception as idx_e:
        print(f"⚠️ No se pudo crear/verificar índice de email: {idx_e}")

    # 🟩 Índice único en user_settings.user_id (preferencias por usuario)
    try:
        client[MONGO_DB_NAME]["user_settings"].create_index("user_id", unique=True)
        print("✅ Índice único en 'user_settings.user_id' creado/verificado")
    except Exception as idx_e2:
        print(f"⚠️ No se pudo crear/verificar índice de user_settings.user_id: {idx_e2}")

except errors.ServerSelectionTimeoutError as e:
    print("❌ Error: No se pudo conectar a MongoDB (timeout)")
    print(e)
    client = None
except Exception as e:
    print("⚠️ Error general al conectar con MongoDB:")
    print(e)
    client = None


# 📦 DB handle
def get_database():
    if client is None:
        raise RuntimeError("❌ Conexión a la base de datos fallida.")
    return client[MONGO_DB_NAME]

# 🔍 Accesos a colecciones
def get_users_collection():
    return get_database()["users"]

def get_logs_collection():
    return get_database()["logs"]

def get_stats_collection():
    return get_database()["statistics"]

def get_intents_collection():
    return get_database()["intents"]

def get_test_logs_collection():
    return get_database()["test_logs"]

def get_user_settings_collection():
    """Colección de preferencias por usuario."""
    return get_database()["user_settings"]