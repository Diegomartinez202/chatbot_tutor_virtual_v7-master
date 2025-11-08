# rasa/actions/acciones_terminar_conversacion_segura.py
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ConversationPaused, ConversationResumed

class ActionVerificarProcesoActivo(Action):
    def name(self) -> Text: return "action_verificar_proceso_activo"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_slot("proceso_activo"):
            dispatcher.utter_message(response="utter_confirmar_cierre_seguro")
        else:
            dispatcher.utter_message(response="utter_confirmar_cierre")
        return [SlotSet("confirmacion_cierre", "pendiente")]

class ActionConfirmarCierreSeguroFinal(Action):
    """Evita colisión de nombre con otras definiciones de ActionConfirmarCierre."""
    def name(self) -> Text: return "action_confirmar_cierre_seguro_final"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_despedida_final")
        return [SlotSet("session_activa", False), SlotSet("confirmacion_cierre", None), SlotSet("proceso_activo", None), ConversationPaused()]

class ActionCancelarCierreSeguro(Action):
    def name(self) -> Text: return "action_cancelar_cierre_seguro"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_cancelar_cierre")
        return [SlotSet("confirmacion_cierre", None), ConversationResumed()]
