# backend/services/test_log_service.py

from backend.db.mongodb import get_database
from models.test_log_model import TestLog

def get_test_logs(limit=50):
    db = get_database()
    logs = db["test_logs"].find().sort("timestamp", -1).limit(limit)
    return [TestLog(**log) for log in logs]