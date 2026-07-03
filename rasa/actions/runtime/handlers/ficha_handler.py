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
    Handler encargado de consultar la ficha académica del estudiante.

    Arquitectura:
        Action -> ActionHandler -> ficha_handler -> Backend
    """

    user_id = tracker.sender_id

    data = safe_backend_response(
        call(
            tracker,
            f"/api/ficha/{user_id}",
            method="GET",
            default={"ficha": []},
        )
    )

    ficha = data.get("ficha", [])

    # Si el backend devuelve un único objeto,
    # lo convertimos en lista para mantener consistencia.
    if isinstance(ficha, dict):
        ficha = [ficha]

    if not ficha:
        dispatcher.utter_message(
            text="📄 No se encontró información de tu ficha académica."
        )
        return []

    dispatcher.utter_message(
        text="📄 Encontré la siguiente información de tu ficha académica."
    )

    items = []

    for f in ficha[:5]:

        numero = (
            f.get("numero")
            or f.get("codigo")
            or f.get("ficha")
            or "Sin número"
        )

        programa = (
            f.get("programa")
            or f.get("nombre_programa")
            or "Programa no disponible"
        )

        estado = (
            f.get("estado")
            or "Sin estado"
        )

        items.append(
            f"📌 Ficha: {numero} | {programa} | Estado: {estado}"
        )

    send_lines(
        dispatcher,
        "📄 Ficha académica:",
        items,
    )

    return ficha