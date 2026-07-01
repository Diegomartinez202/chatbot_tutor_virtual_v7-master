from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

from ...runtime.api_client import call
from .base_handler import safe_backend_response


def handler(
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    payload=None,
):

    user_id = tracker.sender_id

    data = safe_backend_response(
        call(
            tracker,
            f"/api/estudiantes/{user_id}/estado",
            method="GET",
            default={},
        )
    )

    if not data:
        dispatcher.utter_message(
            text="⚠️ No se encontró información del estudiante."
        )
        return {}

    if not isinstance(data, dict):
        dispatcher.utter_message(
            text="⚠️ No fue posible obtener el estado del estudiante."
        )
        return {}

    progreso = data.get("progreso")
    if progreso is None:
        progreso = 0

    estado = data.get("estado") or "desconocido"

    dispatcher.utter_message(
        text=f"📚 Estado: {estado} | Progreso: {progreso}%"
    )

    return data