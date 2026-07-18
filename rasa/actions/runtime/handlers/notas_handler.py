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
    """
    Handler encargado de consultar las notas del estudiante.

    Arquitectura:
        Action -> ActionHandler -> notas_handler -> Backend
    """

    user_id = tracker.sender_id

    data = safe_backend_response(
        call(
            tracker,
            f"/api/notas/{user_id}",
            method="GET",
            default={"notas": []},
        )
    )

    notas = data.get("notas", [])

    if not notas:
        dispatcher.utter_message(
            text="📝 No tienes notas registradas."
        )
        return []

    dispatcher.utter_message(
        text=f"📝 Encontré {len(notas)} nota(s) registrada(s)."
    )

    items = []

    for nota in notas[:5]:

        curso = (
            nota.get("curso")
            or nota.get("materia")
            or "Curso"
        )

        calificacion = (
            nota.get("nota")
            or nota.get("calificacion")
            or "Sin nota"
        )

        periodo = (
            nota.get("periodo")
            or nota.get("corte")
            or "Sin período"
        )

        items.append(
            f"📚 {curso} | Nota: {calificacion} | {periodo}"
        )

    send_lines(
        dispatcher,
        "📝 Notas:",
        items,
    )

    # ==========================================================
    # FIN DEL FLUJO ADMINISTRATIVO
    # ==========================================================

    dispatcher.utter_message(
        response="utter_fin_consulta_academica",
    )

    return []