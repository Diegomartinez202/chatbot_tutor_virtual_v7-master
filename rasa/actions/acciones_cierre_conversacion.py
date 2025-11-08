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
    """Pide confirmación al usuario antes de finalizar la conversación."""

    def name(self) -> Text:
        return "action_confirmar_cierre"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[EventType]:
        # Usa tu respuesta avanzada definida en domain_parts/domain_cierre_conversacion.yml
        dispatcher.utter_message(response="utter_confirmar_cierre")
        return []


class ActionFinalizarConversacion(Action):
    """Cierra la conversación de forma segura."""

    def name(self) -> Text:
        return "action_finalizar_conversacion"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[EventType]:
        dispatcher.utter_message(response="utter_cierre_confirmado")
        # Si tienes encuesta_activa u otros procesos, puedes pausar:
        return [ConversationPaused(), SlotSet("encuesta_activa", False)]


class ActionCancelarCierre(Action):
    """Usuario decide no cerrar; se mantiene el hilo activo."""

    def name(self) -> Text:
        return "action_cancelar_cierre"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[EventType]:
        dispatcher.utter_message(response="utter_cierre_cancelado")
        return []
