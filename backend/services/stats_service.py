from backend.db.mongodb import get_logs_collection, get_users_collection
from collections import defaultdict
from datetime import datetime
from pymongo import DESCENDING
import pytz

tz = pytz.timezone("America/Bogota")

def build_date_filter(desde=None, hasta=None):
    filtro = {}
    if desde or hasta:
        rango = {}
        if desde:
            rango["$gte"] = datetime.strptime(desde, "%Y-%m-%d").replace(tzinfo=tz)
        if hasta:
            rango["$lte"] = datetime.strptime(hasta, "%Y-%m-%d").replace(tzinfo=tz)
        filtro["timestamp"] = rango
    return filtro

async def obtener_total_logs(desde=None, hasta=None):
    filtro = build_date_filter(desde, hasta)
    return get_logs_collection().count_documents(filtro)

async def obtener_total_exportaciones_csv(desde=None, hasta=None):
    filtro = build_date_filter(desde, hasta)
    filtro["tipo"] = "descarga"
    return get_logs_collection().count_documents(filtro)

async def obtener_intents_mas_usados(limit: int = 5, desde=None, hasta=None):
    filtro = build_date_filter(desde, hasta)
    filtro["intent"] = {"$exists": True, "$ne": ""}
    pipeline = [
        {"$match": filtro},
        {"$group": {"_id": "$intent", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    resultados = list(get_logs_collection().aggregate(pipeline))
    return [{"intent": r["_id"], "total": r["count"]} for r in resultados]

async def obtener_total_usuarios():
    return get_users_collection().count_documents({})

async def obtener_ultimos_usuarios(limit: int = 5):
    usuarios = get_users_collection().find({}, {"password": 0}).sort("_id", DESCENDING).limit(limit)
    return [
        {
            "id": str(u["_id"]),
            "email": u["email"],
            "rol": u.get("rol", "usuario"),
            "nombre": u.get("nombre", ""),
        }
        for u in usuarios
    ]

async def obtener_usuarios_por_rol():
    pipeline = [
        {"$group": {"_id": "$rol", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}
    ]
    resultados = list(get_users_collection().aggregate(pipeline))
    return [{"rol": r["_id"], "total": r["total"]} for r in resultados]

async def obtener_logs_por_dia(desde=None, hasta=None):
    filtro = build_date_filter(desde, hasta)
    pipeline = [
        {"$match": filtro},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$timestamp",
                        "timezone": "America/Bogota"
                    }
                },
                "total": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    resultados = list(get_logs_collection().aggregate(pipeline))
    return [{"fecha": r["_id"], "total": r["total"]} for r in resultados]