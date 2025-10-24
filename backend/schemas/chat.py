# backend/schemas/chat.py
from pydantic import BaseModel

class ChatRequest(BaseModel):
    sender_id: str = "anonimo"
    message: str
