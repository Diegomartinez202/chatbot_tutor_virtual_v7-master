# rasa/actions/acciones_menu.py
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

class ActionSetMenuPrincipal(Action):
    def name(self) -> Text: return "action_set_menu_principal"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [SlotSet("menu_actual", "principal")]

class ActionVerEstadoEstudiante(Action):
    def name(self) -> Text: return "action_ver_estado_estudiante"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_slot("is_authenticated"):
            dispatcher.utter_message(text="Aquí está tu estado como estudiante...")
        else:
            dispatcher.utter_message(response="utter_login_requerido")
        return []

class ActionConsultarCertificados(Action):
    def name(self) -> Text: return "action_consultar_certificados"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_slot("is_authenticated"):
            dispatcher.utter_message(text="Aquí tienes tus certificados disponibles...")
        else:
            dispatcher.utter_message(response="utter_login_requerido")
        return []
