from typing import Any, Dict

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

from ...runtime.api_client import call
from .base_handler import (
    safe_backend_response,
    send_lines,
)

MAX_CERTIFICADOS = 5


def handler(
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    payload: Dict = None,
):

    payload = payload or {}

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

    return certificados