# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    EventType,
    SlotSet,
    ConversationPaused,
)
class ActionConfirmarCierre(Action):
    def name(self) -> Text:
        return "action_confirmar_cierre"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        # Muestra confirmación con botones
        dispatcher.utter_message(response="utter_confirmar_cierre")
        return []
class ActionFinalizarConversacion(Action):
    def name(self) -> Text:
        return "action_finalizar_conversacion"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        # Despedida profesional + “volver al menú” por si el canal no corta sesión
        dispatcher.utter_message(response="utter_despedida_profesional")
        dispatcher.utter_message(response="utter_volver_menu")
        return []

class ActionCancelarCierre(Action):
    def name(self) -> Text:
        return "action_cancelar_cierre"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        dispatcher.utter_message(response="utter_cierre_cancelado")
        dispatcher.utter_message(response="utter_volver_menu")
        return []
