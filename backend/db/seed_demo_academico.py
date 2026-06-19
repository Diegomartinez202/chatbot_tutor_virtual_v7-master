#\backend\db\seed_demo_academico.py
from __future__ import annotations
from typing import List, Dict, Any
from dotenv import load_dotenv
load_dotenv()
import os
from pymongo import MongoClient, errors
from backend.config.settings import settings 

from backend.db.mongodb import (
    get_database,
    get_users_chat_collection,
    get_certificados_collection,
    get_horarios_collection,
    get_progreso_cursos_collection,
    get_tutores_collection,
    get_calificaciones_collection,
)

DEMO_USER_ID = "user-123"
MONGO_URI = os.getenv("MONGO_URI") or settings.mongo_uri
MONGO_DB_NAME = settings.mongo_db_name

def seed_users_chat() -> None:
    col = get_users_chat_collection()

    # Dejamos solo el usuario demo para que no se duplique
    col.delete_many({"_id": DEMO_USER_ID})

    col.insert_one({
        "_id": DEMO_USER_ID,
        "email": "estudiante.demo@zajuna.edu",
        "nombre": "Estudiante Demo",
        "tipo_usuario": "chat",
        "estado": "Activo",
        "programa": "Tecnólogo en Gestión Administrativa",
    })
    print("✅ Usuario chat demo creado / actualizado")


def seed_certificados() -> None:
    col = get_certificados_collection()

    # Limpiamos certificados del usuario demo
    col.delete_many({"user_id": DEMO_USER_ID})

    col.insert_many([
        {
            "user_id": DEMO_USER_ID,
            "curso": "Excel Intermedio",
            "fecha": "2025-06-10",
            "url": "https://zajuna.edu/cert/123",
            "tipo": "certificado de estudio",
            "programa": "Excel Intermedio para la oficina",
        },
        {
            "user_id": DEMO_USER_ID,
            "curso": "Programación Básica",
            "fecha": "2025-04-02",
            "url": "https://zajuna.edu/cert/456",
            "tipo": "certificado de estudio",
            "programa": "Introducción a la programación",
        },
    ])
    print("✅ Certificados demo creados / actualizados")


def seed_horarios() -> None:
    col = get_horarios_collection()

    col.delete_many({"user_id": DEMO_USER_ID})

    col.insert_many([
        {
            "user_id": DEMO_USER_ID,
            "curso": "Contabilidad básica",
            "dia": "Lunes",
            "hora": "08:00 - 10:00",
            "aula": "Aula 203",
        },
        {
            "user_id": DEMO_USER_ID,
            "curso": "Administración de recursos humanos",
            "dia": "Miércoles",
            "hora": "10:00 - 12:00",
            "aula": "Aula 105",
        },
    ])
    print("✅ Horarios demo creados / actualizados")


def seed_progreso() -> None:
    col = get_progreso_cursos_collection()

    col.delete_many({"user_id": DEMO_USER_ID})

    col.insert_one({
        "user_id": DEMO_USER_ID,
        "avance_global": 62,
        "cursos": [
            {"nombre": "Excel Intermedio", "avance": 80},
            {"nombre": "Programación Básica", "avance": 45},
        ],
    })
    print("✅ Progreso cursos demo creado / actualizado")


def seed_tutor() -> None:
    col = get_tutores_collection()

    col.delete_many({"user_id": DEMO_USER_ID})

    col.insert_one({
        "user_id": DEMO_USER_ID,
        "nombre": "Ing. María Pérez",
        "contacto": "maria.perez@zajuna.edu",
    })
    print("✅ Tutor demo creado / actualizado")


def seed_calificaciones() -> None:
    col = get_calificaciones_collection()

    col.delete_many({"user_id": {"$in": ["user-123", "user-456"]}})

    docs: List[Dict[str, Any]] = [
        {
            "user_id": "user-123",
            "curso": "Contabilidad básica",
            "nota": 4.2,
        },
        {
            "user_id": "user-123",
            "curso": "Servicio al cliente",
            "nota": 4.8,
        },
        {
            "user_id": "user-456",
            "curso": "Excel Intermedio",
            "nota": 3.9,
        },
    ]

    if docs:
        col.insert_many(docs)

    print("✅ Seed de calificaciones demo insertado correctamente.")


def main() -> None:
    print("🚀 Iniciando seed académico demo...")
    seed_users_chat()
    seed_certificados()
    seed_horarios()
    seed_progreso()
    seed_tutor()
    seed_calificaciones()
    print("🎉 Seed académico completo.")


if __name__ == "__main__":
    main()
