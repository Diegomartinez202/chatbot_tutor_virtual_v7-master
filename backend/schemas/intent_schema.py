from pydantic import BaseModel, Field
from typing import List

# 🧠 Modelo para representar un intent con ejemplos y respuestas
class IntentOut(BaseModel):
    intent: str = Field(..., example="saludo")
    examples: List[str] = Field(..., example=["hola", "buenos días"])
    responses: List[str] = Field(..., example=["¡Hola! ¿En qué puedo ayudarte?"])

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "extra": "ignore",
    }

# 📥 Modelo para entrada de intent (crear/actualizar)
class IntentIn(BaseModel):
    intent: str = Field(..., description="Nombre del intent")
    examples: List[str] = Field(..., description="Ejemplos de frases del intent")
    responses: List[str] = Field(..., description="Respuestas asociadas al intent")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "extra": "ignore",
    }

# ✅ Modelo para importar múltiples intents desde archivo
class IntentsImport(BaseModel):
    intents: List[IntentIn] = Field(..., description="Lista de intents a importar")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "extra": "ignore",
    }