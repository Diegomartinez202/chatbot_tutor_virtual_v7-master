from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ConversationPaused, ConversationResumed
from datetime import datetime
from .acciones_encuesta import ActionRegistrarEncuesta


# ======================================================
# 🚀 AUTORESUME CON PERSISTENCIA EN MONGODB
# ======================================================

class ActionAutoResume(Action):
    def name(self) -> Text:
        return "action_auto_resume"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        encuesta_activa = tracker.get_slot("encuesta_activa")
        usuario = tracker.sender_id

        if encuesta_activa:
            dispatcher.utter_message(
                text=f"👋 Hola {usuario}, parece que dejaste una encuesta sin terminar. ¿Deseas continuar?"
            )
            return [SlotSet("reanudar_pendiente", True)]
        else:
            dispatcher.utter_message(text="👋 ¡Hola! Bienvenido de nuevo. No tienes tareas pendientes.")
            return [SlotSet("reanudar_pendiente", False)]


class ActionReanudarAuto(Action):
    def name(self) -> Text:
        return "action_reanudar_auto"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        if tracker.get_slot("reanudar_pendiente"):
            dispatcher.utter_message(
                text="🔄 Retomando tu encuesta o proceso pendiente donde lo dejaste..."
            )
            return [ConversationResumed()]
        else:
            dispatcher.utter_message(text="Nada pendiente. Continuemos desde el inicio.")
            return []
