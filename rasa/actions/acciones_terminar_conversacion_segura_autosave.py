# rasa/actions/acciones_terminar_conversacion_segura_autosave.py
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ConversationPaused, ConversationResumed
from datetime import datetime

class ActionVerificarProcesoActivoAutosave(Action):
    def name(self) -> Text: return "action_verificar_proceso_activo_autosave"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        proceso_activo     = tracker.get_slot("proceso_activo")
        encuesta_incompleta = tracker.get_slot("encuesta_incompleta")
        if encuesta_incompleta:
            dispatcher.utter_message(response="utter_confirmar_cierre_con_autosave")
        elif proceso_activo:
            dispatcher.utter_message(response="utter_confirmar_cierre_seguro")
        else:
            dispatcher.utter_message(response="utter_confirmar_cierre")
        return [SlotSet("confirmacion_cierre", "pendiente")]

class ActionGuardarEncuestaIncompleta(Action):
    def name(self) -> Text: return "action_guardar_encuesta_incompleta"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        usuario = tracker.sender_id
        fecha   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dispatcher.utter_message(text=f"Guardando tu progreso de encuesta ({fecha}) para el usuario {usuario}…")
        dispatcher.utter_message(text="✅ Encuesta parcial registrada correctamente.")
        return [SlotSet("encuesta_incompleta", False), SlotSet("proceso_activo", None)]

class ActionConfirmarCierreAutosave(Action):
    def name(self) -> Text: return "action_confirmar_cierre_autosave"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_slot("encuesta_incompleta"):
            dispatcher.utter_message(response="utter_despedida_final")
            return [SlotSet("session_activa", False), SlotSet("confirmacion_cierre", None), SlotSet("encuesta_incompleta", False), ConversationPaused()]
        dispatcher.utter_message(response="utter_despedida_sin_guardar")
        return [SlotSet("session_activa", False), SlotSet("confirmacion_cierre", None), ConversationPaused()]

class ActionCancelarCierreAutosave(Action):
    def name(self) -> Text: return "action_cancelar_cierre_autosave"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_cancelar_cierre")
        return [SlotSet("confirmacion_cierre", None), ConversationResumed()]
