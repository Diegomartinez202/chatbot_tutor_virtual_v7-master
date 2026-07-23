
import os
from typing import Any, Dict

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

from ...runtime.api_client import call
from .base_handler import (
    safe_backend_response,
    send_lines,
)

MAX_CERTIFICADOS = 5
# ==========================================================
# MODO DEMOSTRACIÓN
# En sustentación permite mostrar el flujo autenticado sin
# depender de la API real de Zajuna.
# En producción debe permanecer en False.
# ==========================================================

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

def handler(
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    payload: Dict = None,
):

    payload = payload or {}

    # ==========================================================
    # DEMO
    # ==========================================================

    if DEMO_MODE:

        dispatcher.utter_message(
            text="📜 Tienes 2 certificados disponibles."
        )

        send_lines(
            dispatcher,
            "📜 Certificados:",
            [
                "• Certificado de Fundamentos de Programación",
                "• Certificado de Bases de Datos Relacionales",
            ],
        )

        dispatcher.utter_message(
            response="utter_fin_consulta_academica",
        )

        return []
    
    # ==========================================================
    # PRODUCCIÓN
    # ==========================================================

    response = safe_backend_response(
        call(
            tracker,
            "/api/certificados",
            method="GET",
            default={"certificados": []},
        )
    )

    certificados = response.get("certificados") or []

    if not certificados:
        dispatcher.utter_message(
            text="📜 No tienes certificados registrados."
        )

        dispatcher.utter_message(
            response="utter_fin_consulta_academica",
        )

        return []

    dispatcher.utter_message(
        text=f"📜 Tienes {len(certificados)} certificados disponibles."
    )

    items = []

    for certificado in certificados[:MAX_CERTIFICADOS]:

        if not isinstance(certificado, dict):
            continue

        nombre = (
            certificado.get("titulo")
            or certificado.get("nombre")
            or "Certificado"
        )

        items.append(f"• {nombre}")

    send_lines(
        dispatcher,
        "📜 Certificados:",
        items,
    )

    # ==========================================================
    # FIN DEL FLUJO ADMINISTRATIVO
    # ==========================================================

    dispatcher.utter_message(
        response="utter_fin_consulta_academica",
    )

    return []