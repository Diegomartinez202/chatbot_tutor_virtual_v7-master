# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType

MAX_INTENTOS_FORM = 3  # puedes exponerlo vía ENV si lo prefieres

class ActionRegistrarIntentoForm(Action):
    """Incrementa el slot soporte_intentos en 1 durante el form."""

    def name(self) -> Text:
        return "action_registrar_intento_form"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[EventType]:
        intentos = tracker.get_slot("soporte_intentos") or 0
        intentos = int(intentos) + 1
        return [SlotSet("soporte_intentos", intentos)]


class ActionVerificarMaxIntentosForm(Action):
    """Si supera el máximo, la rule correspondiente cortará el form (active_loop: null)."""

    def name(self) -> Text:
        return "action_verificar_max_intentos_form"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[EventType]:
        intentos = int(tracker.get_slot("soporte_intentos") or 0)
        # Si llegó al máximo, dejamos el contador en 0 para futuros intentos
        if intentos >= MAX_INTENTOS_FORM:
            return [SlotSet("soporte_intentos", 0)]
        return []
class ActionOfrecerHumano(Action):
    def name(self) -> Text:
        return "action_ofrecer_humano"

    def run(self, dispatcher, tracker, domain) -> List[EventType]:
        dispatcher.utter_message(response="utter_ofrecer_humano")
        return []

class ActionDerivarYRegistrarHumano(Action):
    def name(self) -> Text:
        return "action_derivar_y_registrar_humano"

    def run(self, dispatcher, tracker, domain) -> List[EventType]:
        # Aquí puedes registrar ticket / enviar correo / llamar API
        dispatcher.utter_message(response="utter_derivando_humano")
        return [SlotSet("derivacion_humano", True)]

class ActionHandoffCancelar(Action):
    def name(self) -> Text:
        return "action_handoff_cancelar"

    def run(self, dispatcher, tracker, domain) -> List[EventType]:
        dispatcher.utter_message(response="utter_derivacion_cancelada")
        return [SlotSet("derivacion_humano", False)]

class ActionDerivarHumanoConfirmada(Action):
    """Se ejecuta tras el 'affirm' del usuario para derivar a humano."""
    def name(self) -> Text:
        return "action_derivar_humano_confirmada"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        # Aquí puedes dejar tu lógica de registro/ticket (si ya la tienes en otra acción, llama esa).
        # Compatibilidad con tu flujo actual:
        dispatcher.utter_message(response="utter_derivar_humano_en_progreso")
        return []

class ActionCancelarDerivacion(Action):
    """Responde cuando el usuario niega la derivación a humano."""
    def name(self) -> Text:
        return "action_cancelar_derivacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        dispatcher.utter_message(response="utter_derivacion_cancelada")
        return []