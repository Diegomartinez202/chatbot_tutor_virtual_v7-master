from typing import Dict

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

from ..api_client import call

from .base_handler import (
    safe_backend_response,
    send_lines
)


def handler(
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    payload: Dict = None
):

    payload = payload or {}

    user_id = tracker.sender_id


    response = safe_backend_response(
        call(
            tracker,
            f"/api/historial-academico/{user_id}",
            method="GET",
            default={
                "historial": []
            }
        )
    )


    historial = response.get(
        "historial",
        []
    )


    if not historial:

        dispatcher.utter_message(
            text=(
                "📚 No encontré historial académico registrado.\n\n"
                "Puedes verificarlo directamente en la plataforma Zajuna."
            )
        )

        return []


    dispatcher.utter_message(
        text=(
            f"📚 Encontré {len(historial)} registros "
            "de historial académico."
        )
    )


    items = []


    for registro in historial[:5]:

        programa = (
            registro.get("programa")
            or registro.get("curso")
            or "Formación"
        )

        estado = (
            registro.get("estado")
            or "Sin estado"
        )


        items.append(
            f"📌 {programa} - {estado}"
        )


    send_lines(
        dispatcher,
        "📚 Historial académico:",
        items
    )


    return historial