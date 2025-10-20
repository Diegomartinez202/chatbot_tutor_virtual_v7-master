from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LogModel(BaseModel):
    user_id: str
    email: str
    rol: str
    endpoint: str
    method: str
    status: int
    timestamp: datetime