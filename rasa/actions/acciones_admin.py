from __future__ import annotations
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType


class ActionReiniciarConversacion(Action):
    def name(self) -> Text:
        return "action_reiniciar_conversacion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        """
        Reinicio "lógico" de la conversación:
        - Aquí podrías limpiar slots críticos.
        - Por ahora enviamos un mensaje y reseteamos algunos básicos.
        """
        dispatcher.utter_message(response="utter_reinicio_confirmado")

        events: List[EventType] = [
            SlotSet("session_activa", True),
            SlotSet("encuesta_incompleta", False),
            SlotSet("proceso_activo", None),
            SlotSet("confirmacion_cierre", None),
        ]

        # Aquí podrías añadir más SlotSet si lo necesitas, por ejemplo:
        # events.append(SlotSet("is_authenticated", False))

        return events


class ActionMostrarToken(Action):
    def name(self) -> Text:
        return "action_mostrar_token"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        """
        Muestra un "token" de usuario.
        Aquí usamos el sender_id como identificador lógico.
        """
        user_token = str(tracker.sender_id)

        dispatcher.utter_message(
            response="utter_token_actual",
            user_token=user_token,
        )

        return [SlotSet("user_token", user_token)]


class ActionPingServidor(Action):
    def name(self) -> Text:
        return "action_ping_servidor"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        """
        Simple ping para verificar que el action server está respondiendo.
        Puede usarse en pruebas automatizadas.
        """
        dispatcher.utter_message(response="utter_ping_ok")
        return []
