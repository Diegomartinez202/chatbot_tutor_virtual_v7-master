from __future__ import annotations
from typing import Any, Dict, List, Text
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType
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
        - Envía mensaje de confirmación.
        - Limpia slots básicos de estado y también el contador de turnos.
        """
        dispatcher.utter_message(response="utter_reinicio_confirmado")

        events: List[EventType] = [
            SlotSet("session_activa", True),
            SlotSet("encuesta_incompleta", False),
            SlotSet("proceso_activo", None),
            SlotSet("confirmacion_cierre", None),
            # 👇 NUEVO: reset de contador y flag de sesión larga
            SlotSet("turnos_conversacion", 0),
            SlotSet("sesion_larga", False),
        ]

        # Si quisieras, aquí podrías también limpiar autenticación, etc.
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
    ) -> List[Dict[Text, Any]]:

        tipo_usuario = tracker.get_slot("slot_tipo_usuario")

        # Si no está definido, asumimos "usuario"
        if not tipo_usuario:
            tipo_usuario = "usuario"

        return [SlotSet("slot_tipo_usuario", tipo_usuario)]

class ActionMostrarToken(Action):
    def name(self) -> Text:
        return "action_mostrar_token"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        tipo_usuario = tracker.get_slot("slot_tipo_usuario")
        user_token = tracker.get_slot("user_token")  # o auth_token, según tu diseño

        # Si por alguna razón viene vacío, evita romper el mensaje
        if not user_token:
            user_token = "N/D"

        # Si es admin → usar utter_token_admin
        if tipo_usuario == "admin":
            dispatcher.utter_message(
                response="utter_token_admin",
                user_token=user_token,
            )
        else:
            # Usuario normal → usar la respuesta estándar
            dispatcher.utter_message(
                response="utter_token_actual",
                user_token=user_token,
            )

        return []
class ActionResetTurnosConversacion(Action):
    """
    Acción independiente para resetear solo el contador de turnos y la marca de sesión larga.
    Útil si quieres llamarla en reglas específicas (p.ej. al iniciar una nueva sesión).
    """

    def name(self) -> Text:
        return "action_reset_turnos_conversacion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        return [
            SlotSet("turnos_conversacion", 0),
            SlotSet("sesion_larga", False),
        ]