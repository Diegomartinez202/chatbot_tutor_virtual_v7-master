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

class ActionSetDefaultTipoUsuario(Action):
    def name(self) -> Text:
        return "action_set_default_tipo_usuario"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[SlotSet]:
        tipo = tracker.get_slot("slot_tipo_usuario")

        # Si no hay tipo definido, asumimos "usuario"
        if not tipo:
            return [SlotSet("slot_tipo_usuario", "usuario")]

        # Si viene algo raro, normalizamos a "usuario"
        if tipo not in ("usuario", "admin"):
            return [SlotSet("slot_tipo_usuario", "usuario")]

        return []


class ActionMostrarToken(Action):
    def name(self) -> Text:
        return "action_mostrar_token"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[SlotSet]:
        tipo = tracker.get_slot("slot_tipo_usuario") or "usuario"
        user_token = tracker.get_slot("user_token") or "TOKEN_DE_EJEMPLO_123"

        if tipo == "admin":
            # Aquí podrías cambiar el origen del token admin si es distinto
            dispatcher.utter_message(
                response="utter_token_admin",
                user_token=user_token,
            )
        else:
            dispatcher.utter_message(
                response="utter_token_actual",
                user_token=user_token,
            )

        return []
