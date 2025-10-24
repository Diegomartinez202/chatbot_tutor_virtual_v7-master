from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List
import io, json, csv

from backend.dependencies.auth import require_role
from backend.services.intent_manager import (
    obtener_intents,
    guardar_intent,
    eliminar_intent,
    intent_ya_existe,
    cargar_intents,
    guardar_intent_csv,
    cargar_intents_automaticamente,
)
from backend.services.train_service import entrenar_chatbot as entrenar_rasa

# ✅ Rate limiting por endpoint (no-op si SlowAPI está deshabilitado)
from backend.rate_limit import limit

router = APIRouter()

# 🔹 1. Listar intents existentes
@router.get("/admin/intents", summary="🧠 Obtener lista de intents")
@limit("30/minute")  # consultas de catálogo
def listar_intents(payload=Depends(require_role(["admin"]))):
    return obtener_intents()

# 🔹 2. Crear nuevo intent desde panel
@router.post("/admin/intents", summary="📥 Crear nuevo intent manualmente")
@limit("10/minute")  # operación de escritura controlada
def crear_intent(data: dict, payload=Depends(require_role(["admin"]))):
    if intent_ya_existe(data.get("intent")):
        raise HTTPException(status_code=400, detail="⚠️ El intent ya existe")
    resultado = guardar_intent(data)
    entrenar_rasa()
    return resultado

# 🔹 3. Eliminar intent por nombre
@router.delete("/admin/intents/{intent_name}", summary="🗑️ Eliminar intent")
@limit("10/minute")  # operación de escritura controlada
def eliminar_intent_por_nombre(intent_name: str, payload=Depends(require_role(["admin"]))):
    return eliminar_intent(intent_name)

# 🔹 4. Recargar intents desde archivo local y reentrenar
@router.post("/admin/intents/recargar", summary="♻️ Recargar intents automáticamente desde archivo")
@limit("3/minute")  # recargas más estrictas
def recargar_intents(payload=Depends(require_role(["admin"]))):
    resultado = cargar_intents_automaticamente()
    entrenar_rasa()
    return resultado

# 🔹 5. Subir archivo CSV/JSON para cargar intents
@router.post("/admin/intents/upload", summary="📂 Subir intents desde archivo CSV o JSON")
@limit("5/minute")  # subidas moderadas
async def subir_archivo_intents(file: UploadFile = File(...), payload=Depends(require_role(["admin"]))):
    content = await file.read()

    if file.filename.endswith(".json"):
        data = json.loads(content)
    elif file.filename.endswith(".csv"):
        decoded = content.decode("utf-8").splitlines()
        reader = csv.DictReader(decoded)
        data = list(reader)
    else:
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado")

    resultado = cargar_intents(data)
    entrenar_rasa()
    return resultado

# 🔹 6. Exportar intents existentes a CSV
@router.get("/admin/intents/export", summary="📤 Exportar intents a CSV", response_class=StreamingResponse)
@limit("10/minute")  # exportaciones controladas
def exportar_intents(payload=Depends(require_role(["admin"]))):
    output = guardar_intent_csv()
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=intents_exportados.csv"},
    )
