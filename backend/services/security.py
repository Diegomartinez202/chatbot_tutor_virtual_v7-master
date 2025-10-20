# backend/services/security.py
from __future__ import annotations
from datetime import datetime, timedelta, timezone

try:
    from backend.db.mongodb import get_database  # type: ignore
    def _col():
        return get_database()["auth_attempts"]
except Exception:
    import os
    from pymongo import MongoClient  # type: ignore
    MONGO_URL = (os.getenv("MONGO_URL") or os.getenv("MONGODB_URL") or "mongodb://localhost:27017").strip()
    MONGO_DB  = (os.getenv("MONGO_DB") or os.getenv("MONGODB_DB") or "chatbot_admin").strip()
    _client = MongoClient(MONGO_URL)
    _db = _client[MONGO_DB]
    def _col():
        return _db["auth_attempts"]

def register_failed_attempt(email: str, ip: str, lock_minutes: int, max_attempts: int):
    now = datetime.now(timezone.utc)
    col = _col()
    doc = col.find_one({"email": email})
    if not doc:
        col.insert_one({"email": email, "fail_count": 1, "ip": ip, "lock_until": None, "updated_at": now})
        return
    cnt = int(doc.get("fail_count", 0)) + 1
    lock_until = doc.get("lock_until")
    if cnt >= max_attempts:
        lock_until = now + timedelta(minutes=lock_minutes)
        cnt = 0
    col.update_one({"email": email}, {"$set": {"fail_count": cnt, "ip": ip, "lock_until": lock_until, "updated_at": now}})

def reset_attempts(email: str):
    _col().update_one({"email": email}, {"$set": {"fail_count": 0, "lock_until": None}})

def is_locked(email: str) -> bool:
    doc = _col().find_one({"email": email})
    if not doc:
        return False
    until = doc.get("lock_until")
    if not until:
        return False
    return datetime.now(timezone.utc) < until