# backend/models/message_model.py
from pydantic import BaseModel
from typing import Literal

class MessageCreate(BaseModel):
    user_id: str
    text: str
    sender: Literal["user", "bot"]
    timestamp: str  # o datetime si prefieres