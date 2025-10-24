# =====================================================
# 🧩 backend/services/exportaciones_service.py
# =====================================================
from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any, Optional
from bson import ObjectId

from backend.db.mongodb import get_database


def _col():
    """
    Obtiene la colección 'exportaciones' de forma perezosa (lazy) y segura.
    Evita fallos por inicialización de Mongo en tiempo de import.
    """
    return get_database()["exportaciones"]


def get_exportaciones(
    desde: Optional[datetime],
    hasta: Optional[datetime],
    usuario: Optional[str],
    tipo: Optional[str],
    skip: int,
    limit: int,
) -> List[Dict[str, Any]]:
    """
    Consulta la colección 'exportaciones' aplicando filtros dinámicos.
    Mantiene compatibilidad total con la versión anterior.
    """
    query: Dict[str, Any] = {}
    if desde and hasta:
        query["fecha"] = {"$gte": desde, "$lte": hasta}
    elif desde:
        query["fecha"] = {"$gte": desde}
    elif hasta:
        query["fecha"] = {"$lte": hasta}

    if usuario:
        query["usuario"] = {"$regex": usuario, "$options": "i"}
    if tipo:
        query["tipo"] = tipo

    exportaciones = (
        _col()
        .find(query)
        .sort("fecha", -1)
        .skip(int(skip or 0))
        .limit(int(limit or 50))
    )

    return [
        {
            "_id": str(e.get("_id", ObjectId())),
            "usuario": e.get("usuario", "desconocido"),
            "tipo": e.get("tipo", "desconocido"),
            "fecha": e.get("fecha").isoformat() if e.get("fecha") else None,
            "archivo": e.get("archivo"),
        }
        for e in exportaciones
    ]
