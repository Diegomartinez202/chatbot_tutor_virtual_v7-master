#!/usr/bin/env python3
import os
import sys
import datetime
from pymongo import MongoClient

# Variables de entorno desde Docker
mongo_url = os.getenv("TRACKER_MONGO_URL", "mongodb://mongo:27017")
mongo_db = os.getenv("TRACKER_MONGO_DB", "rasa")
collection_name = os.getenv("RASA_MODELS_COLLECTION", "trained_models")

model_path = sys.argv[1] if len(sys.argv) > 1 else None

if not model_path or not os.path.exists(model_path):
    print(f"[⚠️] Modelo no encontrado: {model_path}")
    sys.exit(1)

model_name = os.path.basename(model_path)

try:
    client = MongoClient(mongo_url)
    db = client[mongo_db]
    coll = db[collection_name]

    doc = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "model_name": model_name,
        "path": model_path,
        "status": "success"
    }

    coll.insert_one(doc)
    print(f"[✅] Modelo '{model_name}' registrado en MongoDB ({mongo_db}.{collection_name})")

except Exception as e:
    print(f"[❌] Error al registrar modelo en MongoDB: {e}")
    sys.exit(1)
