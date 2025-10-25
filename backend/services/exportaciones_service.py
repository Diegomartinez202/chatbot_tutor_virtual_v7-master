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

    # Rango de fechas (respeta casos con solo desde / solo hasta)
    if desde and hasta:
        query["fecha"] = {"$gte": desde, "$lte": hasta}
    elif desde:
        query["fecha"] = {"$gte": desde}
    elif hasta:
        query["fecha"] = {"$lte": hasta}

    # Filtros opcionales
    if usuario:
        query["usuario"] = {"$regex": usuario, "$options": "i"}
    if tipo:
        query["tipo"] = tipo

    cursor = (
        _col()
        .find(query)
        .sort("fecha", -1)
        .skip(int(skip or 0))
        .limit(int(limit or 50))
    )

    items: List[Dict[str, Any]] = []
    for e in cursor:
        _id = e.get("_id", ObjectId())
        fecha_val = e.get("fecha")
        # Si por alguna razón 'fecha' no es datetime, lo devolvemos como None
        fecha_iso = fecha_val.isoformat() if isinstance(fecha_val, datetime) else None

        items.append(
            {
                "_id": str(_id),
                "usuario": e.get("usuario", "desconocido"),
                "tipo": e.get("tipo", "desconocido"),
                "fecha": fecha_iso,
                "archivo": e.get("archivo"),
            }
        )

    return items