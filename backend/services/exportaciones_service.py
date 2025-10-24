# backend/services/exportaciones_service.py
from datetime import datetime
from bson import ObjectId
from backend.db.mongodb import get_database

# 🔧 Crear handle local seguro (evita errores si Mongo aún no está inicializado)
db = get_database()


def get_exportaciones(desde, hasta, usuario, tipo, skip, limit):
    """
    Consulta la colección 'exportaciones' aplicando filtros dinámicos.
    Mantiene compatibilidad total con la versión anterior.
    """
    query = {}
    if desde and hasta:
        query["fecha"] = {"$gte": desde, "$lte": hasta}
    if usuario:
        query["usuario"] = {"$regex": usuario, "$options": "i"}
    if tipo:
        query["tipo"] = tipo

    exportaciones = (
        db["exportaciones"]
        .find(query)
        .sort("fecha", -1)
        .skip(skip)
        .limit(limit)
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