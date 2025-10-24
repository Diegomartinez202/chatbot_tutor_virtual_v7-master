# backend/services/test_log_service.py

from __future__ import annotations

from typing import List
from backend.db.mongodb import get_database
from backend.models.test_log_model import TestLog


def get_test_logs(limit: int = 50) -> List[TestLog]:
    """
    Devuelve los últimos logs de test ordenados por timestamp desc.
    Mantiene la lógica original, corrigiendo el acceso a la DB.
    """
    db = get_database()
    cursor = db["test_logs"].find().sort("timestamp", -1).limit(int(limit))

    items: List[TestLog] = []
    for doc in cursor:
        # Normalizar _id a string para que el modelo no falle
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        items.append(TestLog(**doc))
    return items