# backend/services/exportaciones_service.py
from backend.db.mongodb import db
from bson import ObjectId
from datetime import datetime

def get_exportaciones(desde, hasta, usuario, tipo, skip, limit):
    query = {}
    if desde and hasta:
        query["fecha"] = {"$gte": desde, "$lte": hasta}
    if usuario:
        query["usuario"] = {"$regex": usuario, "$options": "i"}
    if tipo:
        query["tipo"] = tipo

    exportaciones = db["exportaciones"].find(query).sort("fecha", -1).skip(skip).limit(limit)
    return [
        {
            "_id": str(e["_id"]),
            "usuario": e.get("usuario", "desconocido"),
            "tipo": e.get("tipo", "desconocido"),
            "fecha": e.get("fecha").isoformat() if e.get("fecha") else None,
            "archivo": e.get("archivo", None),
        }
        for e in exportaciones
    ]
