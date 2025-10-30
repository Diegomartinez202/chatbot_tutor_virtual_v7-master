#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de registro de modelos entrenados en MongoDB
---------------------------------------------------
✅ Uso: log_model_train.py <ruta_modelo.tar.gz>
✅ Guarda metadatos del modelo con timestamp ISO, nombre, ruta y estado.
✅ Muestra mensajes en consola (con colores) y, opcionalmente, registra en un log de archivo.
"""

import os
import sys
import datetime
from pymongo import MongoClient

# ─────────────────────────────────────────────
# 🎨 Colores ANSI para mejorar la lectura
# ─────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED   = "\033[91m"
BLUE  = "\033[94m"
RESET = "\033[0m"

def _log_to_file(line: str, logfile: str | None) -> None:
    """
    Escribe una línea en el archivo de log si 'logfile' está definido.
    Crea el directorio si no existe.
    """
    if not logfile:
        return
    try:
        os.makedirs(os.path.dirname(logfile), exist_ok=True)
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(line.rstrip() + "\n")
    except Exception:
        # No interrumpir el flujo por errores de logging a archivo
        pass

def main():
    # ─────────────────────────────────────────────
    # 🌍 Variables de entorno (con defaults seguros)
    # ─────────────────────────────────────────────
    mongo_url        = os.getenv("TRACKER_MONGO_URL", "mongodb://mongo:27017")
    mongo_db         = os.getenv("TRACKER_MONGO_DB", "rasa")
    collection_name  = os.getenv("RASA_MODELS_COLLECTION", "trained_models")

    # Ruta del log opcional (puedes setear RASA_MODELS_LOGFILE=/app/logs/model_registry.log)
    logfile = os.getenv("RASA_MODELS_LOGFILE", "/app/logs/model_registry.log")

    # ─────────────────────────────────────────────
    # 📦 Validar argumento (ruta del modelo)
    # ─────────────────────────────────────────────
    model_path = sys.argv[1] if len(sys.argv) > 1 else None

    print(f"{BLUE}[🔍] Iniciando registro del modelo…{RESET}")
    print(f"  • MONGO_URL: {mongo_url}")
    print(f"  • DB/COL   : {mongo_db}.{collection_name}")
    print(f"  • Modelo   : {model_path}")

    if not model_path or not os.path.exists(model_path):
        msg = f"[⚠️] Modelo no encontrado o ruta inválida: {model_path}"
        print(f"{YELLOW}{msg}{RESET}")
        _log_to_file(msg, logfile)
        sys.exit(1)

    model_name = os.path.basename(model_path)
    timestamp  = datetime.datetime.utcnow().isoformat()

    try:
        # ─────────────────────────────────────────
        # 🔗 Conectar a MongoDB + ping de verificación
        # ─────────────────────────────────────────
        print(f"{BLUE}[🔗] Conectando a MongoDB…{RESET}")
        client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        ok_msg = "[✅] Conexión a MongoDB establecida correctamente"
        print(f"{GREEN}{ok_msg}{RESET}")
        _log_to_file(ok_msg, logfile)

        db   = client[mongo_db]
        coll = db[collection_name]

        # ─────────────────────────────────────────
        # 💾 Documento a insertar (mantiene tu esquema)
        # ─────────────────────────────────────────
        doc = {
            "timestamp"  : timestamp,          
            "model_name" : model_name,
            "model_path" : model_path,        
            "status"     : "success",
        }

        result = coll.insert_one(doc)

        done_msg_1 = f"[💾] Modelo '{model_name}' registrado en MongoDB ({mongo_db}.{collection_name})"
        done_msg_2 = f"    • _id   : {result.inserted_id}"
        done_msg_3 = f"    • Fecha : {timestamp}"
        done_msg_4 = f"    • Ruta  : {model_path}"

        print(f"{GREEN}{done_msg_1}{RESET}")
        print(done_msg_2)
        print(done_msg_3)
        print(done_msg_4)

        _log_to_file(done_msg_1, logfile)
        _log_to_file(done_msg_2, logfile)
        _log_to_file(done_msg_3, logfile)
        _log_to_file(done_msg_4, logfile)

    except Exception as e:
        err = f"[❌] Error al registrar modelo en MongoDB: {e}"
        print(f"{RED}{err}{RESET}")
        _log_to_file(err, logfile)
        sys.exit(1)

if __name__ == "__main__":
    main()
