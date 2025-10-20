# backend/services/message_logger.py
from backend.db.mongodb import get_database
from datetime import datetime

db = get_database()
messages_collection = db["messages"]

def log_message(user_id: str, text: str, sender: str):
    messages_collection.insert_one({
        "user_id": user_id,
        "text": text,
        "sender": sender,
        "timestamp": datetime.utcnow()
    })
