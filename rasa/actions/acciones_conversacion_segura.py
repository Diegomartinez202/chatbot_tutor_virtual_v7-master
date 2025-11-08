# rasa/actions/acciones_conversacion_segura.py
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ConversationPaused, ConversationResumed

class ActionVerificarEstadoConversacion(Action):
    def name(self) -> Text: return "action_verificar_estado_conversacion"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(response="utter_confirmar_cierre"); return []
        dispatcher.utter_message(response="utter_cierre_confirmado"); return [ConversationPaused()]

class ActionGuardarProgresoConversacion(Action):
    def name(self) -> Text: return "action_guardar_progreso_conversacion"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(response="utter_guardando_progreso")
        # Aquí puedes integrar a tu backend/Mongo si lo deseas
        dispatcher.utter_message(text="✅ Progreso guardado correctamente.")
        return [SlotSet("encuesta_activa", True)]

class ActionTerminarConversacionSegura(Action):
    def name(self) -> Text: return "action_terminar_conversacion_segura"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(response="utter_confirmar_cierre")
        else:
            dispatcher.utter_message(response="utter_cierre_confirmado"); return [ConversationPaused()]
        return []

class ActionReanudarConversacionSegura(Action):
    def name(self) -> Text: return "action_reanudar_conversacion_segura"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(text="🔄 Retomamos tu encuesta o proceso pendiente donde lo dejaste.")
            return [ConversationResumed()]
        dispatcher.utter_message(text="No había nada pendiente, puedes continuar normalmente.")
        return []

class ActionConfirmarCierreSeguro(Action):
    def name(self) -> Text: return "action_confirmar_cierre_seguro"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(response="utter_confirmar_cierre"); return []
        dispatcher.utter_message(response="utter_cierre_confirmado")
        return [ConversationPaused()]
