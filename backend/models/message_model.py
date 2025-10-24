from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class MessageCreate(BaseModel):
    """💬 Mensaje enviado o recibido en el chatbot."""
    user_id: str = Field(..., description="ID del usuario asociado al mensaje")
    text: str = Field(..., description="Contenido del mensaje")
    sender: Literal["user", "bot"] = Field(..., description="Remitente del mensaje: user o bot")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Fecha y hora del mensaje")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "extra": "ignore",
    }