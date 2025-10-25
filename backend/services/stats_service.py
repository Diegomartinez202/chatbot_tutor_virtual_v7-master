# =====================================================
# 🧩 backend/services/stats_service.py
# =====================================================
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict

from pymongo import DESCENDING

from backend.db.mongodb import get_logs_collection, get_users_collection

# Timezone used for day grouping and local range parsing
TZ_NAME = "America/Bogota"
LOCAL_TZ = ZoneInfo(TZ_NAME)


def _parse_date_ymd(value: str) -> datetime:
    """
    Parse 'YYYY-MM-DD' into a local datetime at 00:00:00.
    """
    dt = datetime.strptime(value, "%Y-%m-%d")
    return dt.replace(tzinfo=LOCAL_TZ, hour=0, minute=0, second=0, microsecond=0)


def _local_to_utc(dt_local: datetime) -> datetime:
    """
    Convert a local datetime to UTC. If naive, assume LOCAL_TZ.
    """
    if dt_local.tzinfo is None:
        dt_local = dt_local.replace(tzinfo=LOCAL_TZ)
    return dt_local.astimezone(timezone.utc)


def build_date_filter(desde: Optional[str] = None, hasta: Optional[str] = None) -> Dict:
    """
    Build a UTC timestamp filter for Mongo.

    - desde: inclusive start of day (00:00:00 local)
    - hasta: inclusive end of day -> implemented with $lt next day 00:00:00 local

    Result example:
      {"timestamp": {"$gte": start_utc, "$lt": end_utc_exclusive}}
    """
    if not desde and not hasta:
        return {}

    ts_filter: Dict[str, datetime] = {}

    if desde:
        start_local = _parse_date_ymd(desde)
        ts_filter["$gte"] = _local_to_utc(start_local)

    if hasta:
        end_local_next_day = _parse_date_ymd(hasta) + timedelta(days=1)
        ts_filter["$lt"] = _local_to_utc(end_local_next_day)

    return {"timestamp": ts_filter} if ts_filter else {}


# =========================
# Counters and aggregations
# =========================

async def obtener_total_logs(desde: Optional[str] = None, hasta: Optional[str] = None) -> int:
    filtro = build_date_filter(desde, hasta)
    return get_logs_collection().count_documents(filtro)


async def obtener_total_exportaciones_csv(desde: Optional[str] = None, hasta: Optional[str] = None) -> int:
    filtro = build_date_filter(desde, hasta)
    filtro["tipo"] = "descarga"
    return get_logs_collection().count_documents(filtro)


async def obtener_intents_mas_usados(
    limit: int = 5,
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
) -> List[Dict[str, int]]:
    filtro = build_date_filter(desde, hasta)
    filtro["intent"] = {"$exists": True, "$ne": ""}

    pipeline = [
        {"$match": filtro},
        {"$group": {"_id": "$intent", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": int(limit)},
    ]
    resultados = list(get_logs_collection().aggregate(pipeline))
    return [{"intent": r["_id"], "total": r["count"]} for r in resultados]


async def obtener_total_usuarios() -> int:
    return get_users_collection().count_documents({})


async def obtener_ultimos_usuarios(limit: int = 5) -> List[Dict[str, str]]:
    usuarios = (
        get_users_collection()
        .find({}, {"password": 0})
        .sort("_id", DESCENDING)
        .limit(int(limit))
    )
    return [
        {
            "id": str(u["_id"]),
            "email": u.get("email", ""),
            "rol": u.get("rol", "usuario"),
            "nombre": u.get("nombre", ""),
        }
        for u in usuarios
    ]


async def obtener_usuarios_por_rol() -> List[Dict[str, int]]:
    pipeline = [
        {"$group": {"_id": "$rol", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
    ]
    resultados = list(get_users_collection().aggregate(pipeline))
    return [{"rol": r["_id"], "total": r["total"]} for r in resultados]


async def obtener_logs_por_dia(desde: Optional[str] = None, hasta: Optional[str] = None) -> List[Dict[str, int]]:
    """
    Group logs per day using $dateToString with the local timezone.
    """
    filtro = build_date_filter(desde, hasta)
    pipeline = [
        {"$match": filtro},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$timestamp",
                        "timezone": TZ_NAME,
                    }
                },
                "total": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    resultados = list(get_logs_collection().aggregate(pipeline))
    return [{"fecha": r["_id"], "total": r["total"]} for r in resultados]