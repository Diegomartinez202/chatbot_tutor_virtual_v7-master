from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType
from .acciones_encuesta import ActionRegistrarEncuesta
from rasa_sdk.events import FollowupAction
import logging

logger = logging.getLogger(__name__)

class ActionGuardarProgresoEncuesta(Action):
    def name(self) -> Text:
        return "action_guardar_progreso_encuesta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
       
        logger.info(
            "[GUARDAR_PROGRESO] encuesta_incompleta=%s encuesta_activa=%s proceso_activo=%s",
             tracker.get_slot("encuesta_incompleta"),
             tracker.get_slot("encuesta_activa"),
             tracker.get_slot("proceso_activo"),
        )

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

        # ¿La encuesta quedó pendiente porque el usuario eligió "Seguir tema"?
        if tracker.get_slot("encuesta_incompleta"):

            logger.info(
                "[ENCUESTA] Reanudando pregunta de resolución."
            )

            return [

                SlotSet(
                    "encuesta_activa",
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

                FollowupAction(
                    "action_preguntar_resolucion",
                ),

            ]

        # Si no había encuesta pendiente, continúa el cierre normal.

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