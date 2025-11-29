# ruta: rasa/actions/acciones_cierre_conversacion.py
from __future__ import annotations
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType


class ActionAnalizarEstadoUsuario(Action):

    def name(self) -> Text:
        return "action_analizar_estado_usuario"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        ultima_emocion = tracker.get_slot("emocion_detectada")

        if ultima_emocion in ["frustrado", "confundido"]:
            dispatcher.utter_message(response="utter_ofrecer_contacto_tutor")

        return []
