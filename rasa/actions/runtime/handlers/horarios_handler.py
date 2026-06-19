from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

from ...runtime.api_client import call
from .base_handler import (
    safe_backend_response,
    send_lines
)
def handler(dispatcher: CollectingDispatcher, tracker: Tracker, payload=None):

    user_id = tracker.sender_id

    data = safe_backend_response(
        call(
            tracker,
            f"/api/horarios/{user_id}",
            method="GET",
            default={"horarios": []}
        )
    )

    horarios = data.get("horarios", [])

    if not horarios:
        dispatcher.utter_message(text="📅 No hay horarios disponibles.")
        return

    dispatcher.utter_message(
        text=f"📅 Tienes {len(horarios)} clases programadas."
    )

    items = []

    for h in horarios[:5]:

        curso = h.get("curso", "Curso")
        hora = h.get("hora", "Sin hora")

        items.append(
            f"📌 {curso} - {hora}"
        )

    send_lines(
        dispatcher,
        "📅 Horarios:",
        items
    )

    return horarios