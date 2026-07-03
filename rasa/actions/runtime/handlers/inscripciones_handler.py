from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

from ...runtime.api_client import call
from .base_handler import (
    safe_backend_response,
    send_lines,
)


def handler(
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    payload=None,
):

    user_id = tracker.sender_id

    data = safe_backend_response(
        call(
            tracker,
            f"/api/inscripciones/{user_id}",
            method="GET",
            default={"inscripciones": []},
        )
    )

    inscripciones = data.get("inscripciones", [])

    if not inscripciones:
        dispatcher.utter_message(
            text="📝 No tienes inscripciones registradas."
        )
        return

    dispatcher.utter_message(
        text=f"📝 Tienes {len(inscripciones)} inscripción(es) registrada(s)."
    )

    items = []

    for inscripcion in inscripciones[:5]:

        curso = (
            inscripcion.get("curso")
            or inscripcion.get("materia")
            or "Curso"
        )

        estado = inscripcion.get(
            "estado",
            "Sin estado",
        )

        items.append(
            f"📌 {curso} - {estado}"
        )

    send_lines(
        dispatcher,
        "📝 Inscripciones:",
        items,
    )

    return inscripciones