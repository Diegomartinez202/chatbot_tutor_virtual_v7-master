from __future__ import annotations
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType


MAX_INTENTOS_FORM = 3  # ← puedes mover a settings si quieres


class ActionRegistrarIntentoForm(Action):
    """Incrementa el slot soporte_intentos en 1 durante el form."""

    def name(self) -> Text:
        return "action_registrar_intento_form"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[EventType]:
        intentos = tracker.get_slot("soporte_intentos") or 0
        intentos = int(intentos) + 1
        # No hablo al usuario aquí; se encarga la rule con un utter
        return [SlotSet("soporte_intentos", intentos)]


class ActionVerificarMaxIntentosForm(Action):
    """Si supera el máximo, cancelamos el form devolviendo active_loop: null desde rules."""

    def name(self) -> Text:
        return "action_verificar_max_intentos_form"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[EventType]:
        intentos = int(tracker.get_slot("soporte_intentos") or 0)
        if intentos >= MAX_INTENTOS_FORM:
            # Reset contador para futuras sesiones y regresar control
            return [SlotSet("soporte_intentos", 0)]
        # Si no alcanzó el máximo, no hacemos nada (las rules siguen el loop)
        return []
