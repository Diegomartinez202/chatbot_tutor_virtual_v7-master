# ruta: rasa/actions/acciones_seguridad.py
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ConversationPaused, EventType

from .acciones_encuesta import ActionRegistrarEncuesta
import logging

logger = logging.getLogger(__name__)

class ActionVerificarEstadoEncuestaSegura(Action):

    def name(self) -> Text:
        return "action_verificar_estado_encuesta_segura"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        encuesta_activa = bool(
            tracker.get_slot("encuesta_activa")
        )

        logger.info(
            "[SAFE_EXIT_CHECK] encuesta_activa=%s",
            encuesta_activa,
        )

        if encuesta_activa:
            dispatcher.utter_message(
                response="utter_confirmar_cierre_seguro"
            )
            return []

        dispatcher.utter_message(
            response="utter_cierre_confirmado_seguro"
        )

        return [ConversationPaused()]


class ActionGuardarProgresoEncuesta(Action):

    def name(self) -> Text:
        return "action_guardar_progreso_encuesta"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        dispatcher.utter_message(
            response="utter_guardando_progreso"
        )

        latest = tracker.latest_message or {}

        encuesta_data = {
            "usuario": tracker.sender_id,
            "estado": "pendiente",
            "tipo": tracker.get_slot("encuesta_tipo"),
            "comentario": latest.get("text"),
        }

        try:

            if hasattr(
                ActionRegistrarEncuesta,
                "registrar_en_base",
            ):
                ActionRegistrarEncuesta().registrar_en_base(
                    encuesta_data
                )

            logger.info(
                "[ENCUESTA_SAVE] usuario=%s",
                tracker.sender_id,
            )

        except Exception:
            logger.exception(
                "[ENCUESTA_SAVE_ERROR]"
            )

        return [
            SlotSet("encuesta_activa", False)
        ]

class ActionTerminarConversacionSegura(Action):

    def name(self) -> Text:
        return "action_terminar_conversacion_segura"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        logger.info(
            "[SAFE_CONVERSATION_END] user=%s",
            tracker.sender_id,
        )

        dispatcher.utter_message(
            response="utter_cierre_confirmado_seguro"
        )

        return [
            SlotSet("encuesta_activa", False),
            ConversationPaused(),
        ]


