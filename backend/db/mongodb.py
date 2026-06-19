# backend/db/mongodb.py
from __future__ import annotations

from pymongo import MongoClient, errors
from backend.config.settings import settings 

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

    try:
        client[MONGO_DB_NAME]["users"].create_index("email", unique=True)
        print("✅ Índice único en 'email' creado/verificado")
    except Exception as idx_e:
        print(f"⚠️ No se pudo crear/verificar índice de email: {idx_e}")

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


def get_database():
    if client is None:
        raise RuntimeError("❌ Conexión a la base de datos fallida.")
    return client[MONGO_DB_NAME]

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

def get_users_chat_collection():
    return get_database()["users_chat"]

def get_certificados_collection():
    return get_database()["certificados"]

def get_horarios_collection():
    return get_database()["horarios"]

def get_progreso_cursos_collection():
    return get_database()["progreso_cursos"]

def get_tutores_collection():
    return get_database()["tutores"]

def get_calificaciones_collection():
    return get_database()["calificaciones"]

try:
    db = get_database()
    db["users_chat"].create_index("email")
    db["certificados"].create_index("user_id")
    db["horarios"].create_index("user_id")
    db["progreso_cursos"].create_index("user_id")
    db["tutores"].create_index("user_id")
    db["calificaciones"].create_index("user_id")  

    print("✅ Índices básicos creados/verificados para colecciones académicas")
except Exception as e:
    print(f"⚠️ No se pudieron crear índices académicos: {e}")
