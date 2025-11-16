# ruta: rasa/actions/acciones_cierre_conversacion.py
from __future__ import annotations
from typing import Any, Dict, List, Text
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType

class ActionConfirmarCierre(Action):
    def name(self) -> Text:
        return "action_confirmar_cierre"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        dispatcher.utter_message(response="utter_confirmar_cierre")
        return []

class ActionFinalizarConversacion(Action):

    def name(self) -> Text:
        return "action_finalizar_conversacion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # Log sencillo
        print(
            f"[FIN CONVERSACIÓN] user_id={tracker.sender_id} "
            f"last_intent={tracker.latest_message.get('intent', {}).get('name')}"
        )

        # Mensaje de cierre profesional
        dispatcher.utter_message(response="utter_despedida_profesional")

        # 👇 Aquí puedes resetear lo básico
        events: List[Dict[Text, Any]] = [
            SlotSet("encuesta_activa", None),
            SlotSet("escalar_humano", False),
            # añade otros slots que quieras limpiar globalmente
        ]

        # Si quieres conservar la lógica antigua de "reset seguro", puedes encadenarla:
        # events.append(FollowupAction("action_reset_conversacion_segura"))

        return events

class ActionCancelarCierre(Action):
    def name(self) -> Text:
        return "action_cancelar_cierre"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        dispatcher.utter_message(response="utter_cierre_cancelado")
        dispatcher.utter_message(response="utter_volver_menu")
        return []

class ActionAnalizarEstadoUsuario(Action):

    def name(self):
        return "action_analizar_estado_usuario"

    def run(self, dispatcher, tracker, domain):
        ultima_emocion = tracker.get_slot("emocion_detectada")

        if ultima_emocion in ["frustrado", "confundido"]:
            dispatcher.utter_message(response="utter_ofrecer_contacto_tutor")

        return []