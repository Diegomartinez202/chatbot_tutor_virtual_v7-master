# backend/schemas/intent.py
from pydantic import BaseModel, Field
from typing import List

# 🧠 Modelo para representar un intent con ejemplos y respuestas
class IntentOut(BaseModel):
    intent: str = Field(..., example="saludo")
    examples: List[str] = Field(..., example=["hola", "buenos días"])
    responses: List[str] = Field(..., example=["¡Hola! ¿En qué puedo ayudarte?"])

# 📥 Modelo para entrada de intent (crear/actualizar)
class IntentIn(BaseModel):
    intent: str
    examples: List[str]
    responses: List[str]

# ✅ Modelo para importar múltiples intents desde archivo
class IntentsImport(BaseModel):
    intents: List[IntentIn]
