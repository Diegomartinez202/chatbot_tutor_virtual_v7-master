from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ConversationPaused
from .acciones_encuesta import ActionRegistrarEncuesta

class ActionVerificarEstadoEncuesta(Action):
    def name(self) -> Text:
        return "action_verificar_estado_encuesta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        encuesta_activa = tracker.get_slot("encuesta_activa")
        if encuesta_activa:
            dispatcher.utter_message(response="utter_confirmar_cierre")
        else:
            dispatcher.utter_message(response="utter_cierre_confirmado")
            return [ConversationPaused()]
        return []

class ActionGuardarProgresoEncuesta(Action):
    def name(self) -> Text:
        return "action_guardar_progreso_encuesta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(response="utter_guardando_progreso")

        # 🔗 Conecta con ActionRegistrarEncuesta para persistencia real
        encuesta_data = {
            "usuario": tracker.sender_id,
            "estado": "pendiente",
            "tipo": tracker.get_slot("encuesta_activa"),
            "comentario": tracker.latest_message.get("text")
        }
        ActionRegistrarEncuesta().registrar_en_base(encuesta_data)

        return [SlotSet("encuesta_activa", False)]

class ActionTerminarConversacionSegura(Action):
    def name(self) -> Text:
        return "action_terminar_conversacion_segura"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        encuesta_activa = tracker.get_slot("encuesta_activa")

        if encuesta_activa:
            return [SlotSet("encuesta_activa", True)]
        else:
            dispatcher.utter_message(response="utter_cierre_confirmado")
            return [ConversationPaused()]


class ActionIrMenuPrincipal(Action):
    def name(self) -> Text:
        return "action_ir_menu_principal"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(response="utter_menu_principal")
        return []
