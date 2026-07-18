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
            f"/api/tutores/asignado/{user_id}",
            method="GET",
            default={}
        )
    )

    tutor = data.get("tutor")

    if not tutor:
        dispatcher.utter_message(
            text="👨‍🏫 No tienes tutor asignado aún."
        )

        dispatcher.utter_message(
            response="utter_fin_consulta_academica"
        )

        return {}

    nombre = tutor.get("nombre", "Tutor asignado")

    dispatcher.utter_message(
        text=f"👨‍🏫 Tu tutor asignado es {nombre}"
    )

    dispatcher.utter_message(
        response="utter_fin_consulta_academica"
    )

    return data