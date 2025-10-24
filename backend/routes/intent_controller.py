from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from typing import List
import io
import json
import csv

from backend.dependencies.auth import require_role
from backend.services.log_service import log_access
from backend.services.intent_manager import (
    obtener_intents,
    guardar_intent,
    eliminar_intent,
    intent_ya_existe,
    cargar_intents,
    guardar_intent_csv,            # wrapper que devuelve el CSV (StringIO)
    cargar_intents_automaticamente
)
from backend.services.train_service import entrenar_chatbot as entrenar_rasa

# ✅ Rate limiting por endpoint (no-op si SlowAPI está deshabilitado)
from backend.rate_limit import limit

router = APIRouter()


def _ip(request: Request) -> str:
    return getattr(request.state, "ip", None) or (request.client.host if request.client else "unknown")


def _ua(request: Request) -> str:
    return getattr(request.state, "user_agent", None) or request.headers.get("user-agent", "")


# 🔹 1. Listar intents existentes
@router.get("/admin/intents", summary="🧠 Obtener lista de intents")
@limit("30/minute")  # consultas frecuentes
def listar_intents(request: Request, payload=Depends(require_role(["admin"]))):
    log_access(
        user_id=payload["_id"],
        email=payload["email"],
        rol=payload["rol"],
        endpoint="/admin/intents",
        method="GET",
        status=200,
        ip=_ip(request),
        user_agent=_ua(request),
    )
    return obtener_intents()


# 🔹 2. Crear nuevo intent desde panel
@router.post("/admin/intents", summary="📥 Crear nuevo intent manualmente")
@limit("10/minute")  # creación controlada
def crear_intent(request: Request, data: dict, payload=Depends(require_role(["admin"]))):
    if intent_ya_existe(data.get("intent", "")):
        log_access(
            user_id=payload["_id"],
            email=payload["email"],
            rol=payload["rol"],
            endpoint="/admin/intents",
            method="POST",
            status=400,
            ip=_ip(request),
            user_agent=_ua(request),
        )
        raise HTTPException(status_code=400, detail="⚠️ El intent ya existe")

    resultado = guardar_intent(data)
    # Entrenamiento tras crear
    entrenar_rasa()

    log_access(
        user_id=payload["_id"],
        email=payload["email"],
        rol=payload["rol"],
        endpoint="/admin/intents",
        method="POST",
        status=201,
        ip=_ip(request),
        user_agent=_ua(request),
    )

    return resultado


# 🔹 3. Eliminar intent por nombre
@router.delete("/admin/intents/{intent_name}", summary="🗑️ Eliminar intent")
@limit("10/minute")
def eliminar_intent_por_nombre(intent_name: str, request: Request, payload=Depends(require_role(["admin"]))):
    resultado = eliminar_intent(intent_name)

    log_access(
        user_id=payload["_id"],
        email=payload["email"],
        rol=payload["rol"],
        endpoint=f"/admin/intents/{intent_name}",
        method="DELETE",
        status=200,
        ip=_ip(request),
        user_agent=_ua(request),
    )

    return resultado


# 🔹 4. Recargar intents desde archivo local y reentrenar
@router.post("/admin/intents/recargar", summary="♻️ Recargar intents automáticamente desde archivo")
@limit("3/minute")  # reentreno costoso
def recargar_intents(request: Request, payload=Depends(require_role(["admin"]))):
    resultado = cargar_intents_automaticamente()
    entrenar_rasa()

    log_access(
        user_id=payload["_id"],
        email=payload["email"],
        rol=payload["rol"],
        endpoint="/admin/intents/recargar",
        method="POST",
        status=200,
        ip=_ip(request),
        user_agent=_ua(request),
    )

    return resultado


# 🔹 5. Subir archivo CSV/JSON para cargar intents (bulk)
@router.post("/admin/intents/upload", summary="📂 Subir intents desde archivo CSV o JSON")
@limit("5/minute")  # subida moderada
async def subir_archivo_intents(request: Request, file: UploadFile = File(...), payload=Depends(require_role(["admin"]))):
    content = await file.read()

    if file.filename.endswith(".json"):
        data = json.loads(content)
        if not isinstance(data, list):
            raise HTTPException(status_code=400, detail="El JSON debe ser una lista de intents.")
    elif file.filename.endswith(".csv"):
        decoded = content.decode("utf-8").splitlines()
        reader = csv.DictReader(decoded)
        data = list(reader)
    else:
        log_access(
            user_id=payload["_id"],
            email=payload["email"],
            rol=payload["rol"],
            endpoint="/admin/intents/upload",
            method="POST",
            status=400,
            ip=_ip(request),
            user_agent=_ua(request),
        )
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado")

    resultado = cargar_intents(data)
    # Entrenamiento tras cargar
    entrenar_rasa()

    log_access(
        user_id=payload["_id"],
        email=payload["email"],
        rol=payload["rol"],
        endpoint="/admin/intents/upload",
        method="POST",
        status=201,
        ip=_ip(request),
        user_agent=_ua(request),
    )

    return resultado


# 🔹 6. Exportar intents existentes a CSV
@router.get("/admin/intents/export", summary="📤 Exportar intents a CSV", response_class=StreamingResponse)
@limit("10/minute")  # export costoso
def exportar_intents(request: Request, payload=Depends(require_role(["admin"]))):
    output = guardar_intent_csv()  # devuelve StringIO

    log_access(
        user_id=payload["_id"],
        email=payload["email"],
        rol=payload["rol"],
        endpoint="/admin/intents/export",
        method="GET",
        status=200,
        ip=_ip(request),
        user_agent=_ua(request),
    )

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=intents_exportados.csv"},
    )