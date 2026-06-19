# =====================================================
# 🧩 backend/services/security.py
# =====================================================
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

# 🚦 Preferimos usar la conexión centralizada…
try:
    from backend.db.mongodb import get_database  # type: ignore

    def _col():
        return get_database()["auth_attempts"]

except Exception:
    # …pero mantenemos tu fallback para no romper entornos locales sin backend.db
    import os
    from pymongo import MongoClient  # type: ignore

    MONGO_URL = (os.getenv("MONGO_URL") or os.getenv("MONGODB_URL") or "mongodb://localhost:27017").strip()
    MONGO_DB = (os.getenv("MONGO_DB") or os.getenv("MONGODB_DB") or "chatbot_admin").strip()
    _client = MongoClient(MONGO_URL)
    _db = _client[MONGO_DB]

    # Crear índice útil (no falla si ya existe)
    try:
        _db["auth_attempts"].create_index("email", unique=False)
    except Exception:
        pass

    def _col():
        return _db["auth_attempts"]


def register_failed_attempt(email: str, ip: str, lock_minutes: int, max_attempts: int) -> None:
    """
    Registra un intento fallido y bloquea temporalmente si supera el umbral.
    Conserva tu lógica, con tiempos en UTC conscientes de zona.
    """
    now = datetime.now(timezone.utc)
    col = _col()
    doc = col.find_one({"email": email})

    if not doc:
        col.insert_one({
            "email": email,
            "fail_count": 1,
            "ip": ip,
            "lock_until": None,
            "updated_at": now,
        })
        return

    cnt = int(doc.get("fail_count", 0)) + 1
    lock_until = doc.get("lock_until")
    if cnt >= max_attempts:
        lock_until = now + timedelta(minutes=lock_minutes)
        cnt = 0  # reinicia el contador tras aplicar lock

    col.update_one(
        {"email": email},
        {"$set": {"fail_count": cnt, "ip": ip, "lock_until": lock_until, "updated_at": now}}
    )


def reset_attempts(email: str) -> None:
    _col().update_one({"email": email}, {"$set": {"fail_count": 0, "lock_until": None}})


def is_locked(email: str) -> bool:
    """
    Retorna True si el usuario está bloqueado actualmente.
    Admite datetimes naive guardados previamente (los interpreta como UTC).
    """
    doc = _col().find_one({"email": email})
    if not doc:
        return False

    until = doc.get("lock_until")
    if not until:
        return False

    # Normalizar a aware UTC si viniera naive
    if getattr(until, "tzinfo", None) is None:
        until = until.replace(tzinfo=timezone.utc)

    return datetime.now(timezone.utc) < until
