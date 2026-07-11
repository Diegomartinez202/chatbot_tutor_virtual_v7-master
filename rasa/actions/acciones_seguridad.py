from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType
from .acciones_encuesta import ActionRegistrarEncuesta
import logging

logger = logging.getLogger(__name__)

class ActionGuardarProgresoEncuesta(Action):
    def name(self) -> Text:
        return "action_guardar_progreso_encuesta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        dispatcher.utter_message(response="utter_guardando_progreso")
        
        encuesta_data = {
            "usuario": tracker.sender_id,
            "estado": "pendiente",
            "tipo": tracker.get_slot("encuesta_tipo"),
            "comentario": (tracker.latest_message or {}).get("text", "Sin comentarios"),
        }

        try:
            if hasattr(ActionRegistrarEncuesta, "registrar_en_base"):
                ActionRegistrarEncuesta().registrar_en_base(encuesta_data)
                logger.info("[ENCUESTA_SAVE] usuario=%s", tracker.sender_id)
        except Exception:
            logger.exception("[ENCUESTA_SAVE_ERROR]")

        return [

            SlotSet(
                "encuesta_activa",
                False,
            ),

            SlotSet(
                "encuesta_incompleta",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),
            SlotSet(
                "proceso_activo",
                None,
            ),

        ]