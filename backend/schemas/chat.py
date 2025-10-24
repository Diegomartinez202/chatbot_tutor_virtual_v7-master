from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """
    📩 Solicitud enviada al chatbot.
    """
    sender_id: str = Field(default="anonimo", description="Identificador del remitente (usuario, sesión o 'anonimo')")
    message: str = Field(..., description="Texto del mensaje enviado al chatbot")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "extra": "ignore",
    }