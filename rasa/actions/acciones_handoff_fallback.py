from __future__ import annotations
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType

# Puedes mover esto a variables de entorno si lo prefieres:
MAX_INTENTOS_FORM = 3


class ActionRegistrarIntentoForm(Action):
    """Incrementa el slot soporte_intentos en 1 durante el form."""

    def name(self) -> Text:
        return "action_registrar_intento_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        intentos = int(tracker.get_slot("soporte_intentos") or 0)
        intentos += 1
        # No se habla al usuario aquí; los mensajes se manejan en las rules/utters
        return [SlotSet("soporte_intentos", intentos)]


class ActionVerificarMaxIntentosForm(Action):
    """Si supera el máximo, resetea contador (para futuras sesiones).
    La lógica de derivar a humano la manejan las rules al ver soporte_intentos=0.
    """

    def name(self) -> Text:
        return "action_verificar_max_intentos_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        intentos = int(tracker.get_slot("soporte_intentos") or 0)
        # Si llegó al tope, reseteamos para que próximas interacciones no hereden el límite
        if intentos >= MAX_INTENTOS_FORM:
            return [SlotSet("soporte_intentos", 0)]
        # Si no alcanzó el máximo, no hacemos nada especial
        return []
