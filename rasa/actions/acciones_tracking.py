# /app/actions/acciones_tracking.py

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


# Umbral para marcar una sesión como "larga"
SESION_LARGA_UMBRAL = 8  # puedes cambiarlo si quieres


class ActionIncrementarTurnosConversacion(Action):
    def name(self) -> Text:
        return "action_incrementar_turnos_conversacion"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        """
        Incrementa el slot `turnos_conversacion` y marca `sesion_larga` cuando
        supera el umbral SESION_LARGA_UMBRAL.
        - turnos_conversacion: float (influence_conversation: false)
        - sesion_larga: bool (influence_conversation: false)
        """

        # Leer valor actual del slot
        turnos_actual = tracker.get_slot("turnos_conversacion") or 0.0

        try:
            turnos_actual = float(turnos_actual)
        except (TypeError, ValueError):
            turnos_actual = 0.0

        nuevo_valor = turnos_actual + 1.0

        # Calcular si la sesión ya se considera larga
        sesion_larga = tracker.get_slot("sesion_larga") or False
        try:
            sesion_larga = bool(sesion_larga)
        except Exception:
            sesion_larga = False

        if nuevo_valor >= SESION_LARGA_UMBRAL:
            sesion_larga = True

        # No enviamos ningún mensaje al usuario, solo actualizamos slots
        return [
            SlotSet("turnos_conversacion", nuevo_valor),
            SlotSet("sesion_larga", sesion_larga),
        ]
