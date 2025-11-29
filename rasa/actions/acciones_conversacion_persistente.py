# ruta: rasa/actions/acciones_conversacion_persistente.py
from __future__ import annotations
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ConversationResumed, EventType


class ActionAutoResume(Action):
    def name(self) -> Text:
        return "action_auto_resume"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        encuesta_activa = bool(tracker.get_slot("encuesta_activa"))
        usuario = tracker.sender_id or "usuario"

        if encuesta_activa:
            # Marca que hay algo por reanudar y pregunta
            dispatcher.utter_message(
                text=f"👋 Hola {usuario}, parece que dejaste una encuesta sin terminar."
            )
            dispatcher.utter_message(response="utter_reanudar_auto")
            return [SlotSet("reanudar_pendiente", True)]

        # Sin pendientes
        dispatcher.utter_message(response="utter_bienvenida_auto")
        return [SlotSet("reanudar_pendiente", False)]


class ActionReanudarAuto(Action):
    def name(self) -> Text:
        return "action_reanudar_auto"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        if bool(tracker.get_slot("reanudar_pendiente")):
            dispatcher.utter_message(
                text="🔄 Retomando tu encuesta o proceso pendiente donde lo dejaste..."
            )
            # Puedes disparar aquí un FollowupAction al formulario/flujo que corresponda.
            return [ConversationResumed(), SlotSet("reanudar_pendiente", False)]

        dispatcher.utter_message(
            text="No hay procesos pendientes. Continuemos desde el inicio."
        )
        return []
