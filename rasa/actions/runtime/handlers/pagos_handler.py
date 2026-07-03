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
    Handler encargado de consultar los pagos del estudiante.

    Arquitectura:
        Action -> ActionHandler -> pagos_handler -> Backend
    """

    user_id = tracker.sender_id

    data = safe_backend_response(
        call(
            tracker,
            f"/api/pagos/{user_id}",
            method="GET",
            default={"pagos": []},
        )
    )

    pagos = data.get("pagos", [])

    if not pagos:
        dispatcher.utter_message(
            text="💳 No tienes pagos registrados."
        )
        return []

    dispatcher.utter_message(
        text=f"💳 Encontré {len(pagos)} pago(s) registrado(s)."
    )

    items = []

    for pago in pagos[:5]:

        concepto = (
            pago.get("concepto")
            or pago.get("descripcion")
            or "Concepto no disponible"
        )

        valor = (
            pago.get("valor")
            or pago.get("monto")
            or "Sin valor"
        )

        estado = (
            pago.get("estado")
            or "Sin estado"
        )

        items.append(
            f"💰 {concepto} | {valor} | {estado}"
        )

    send_lines(
        dispatcher,
        "💳 Pagos:",
        items,
    )

    return pagos