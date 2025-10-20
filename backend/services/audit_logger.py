from datetime import datetime
from backend.db.mongodb import get_logs_collection

def log_access(user_id: str, email: str, rol: str, endpoint: str, method: str, status: int):
    log = {
        "user_id": user_id,
        "email": email,
        "rol": rol,
        "endpoint": endpoint,
        "method": method,
        "status": status,
        "timestamp": datetime.utcnow()
    }
    get_logs_collection().insert_one(log)