# ruta: rasa/actions/acciones_academico.py

from __future__ import annotations

import logging
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import (
    SlotSet,
    ActiveLoop,
    FollowupAction,
    UserUtteranceReverted,
)
from .runtime.action_handler import action_handler
from typing import Any, Dict, List, Optional, Text
from rasa_sdk.events import EventType
from .core.llm_engine import run_llm
from .core.nlp_utils import detectar_materia
from .core.prompts import MATERIAS
logger = logging.getLogger(__name__)

# ================================================================
# 🚀 BOOTSTRAP SAFE
# ================================================================

try:
    if not action_handler.registry:
        action_handler.bootstrap()
except Exception:
    logger.exception("[ACADEMICO] error bootstrap ActionHandler")


def validar_autenticacion(
    tracker: Tracker,
    pending_action: str,
) -> Optional[List[EventType]]:
    """
    Verifica si el usuario está autenticado.

    Si no lo está, prepara el flujo de autenticación para que
    ActionHandleWithLLM explique el proceso y recuerde la acción
    que el usuario intentaba ejecutar.
    """

    if tracker.get_slot("is_authenticated") is True:
        return None

    return [
        SlotSet(
            "requires_auth",
            True,
        ),
        SlotSet(
            "pending_action",
            pending_action,
        ),
        FollowupAction(
            "action_handle_with_llm",
        ),
    ]

# ================================================================
# 🧠 EXECUTOR CENTRAL
# ================================================================

def _exec(
    action_name: str,
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
) -> List[Any]:

    logger.info(
        "[ACADEMICO] execute=%s user=%s",
        action_name,
        tracker.sender_id,
    )

    try:
        result = action_handler.execute(
            action_name=action_name,
            dispatcher=dispatcher,
            tracker=tracker,
            payload={},
        )

        if isinstance(result, list):
            return result

        return []

    except Exception:
        logger.exception(
            "[ACADEMICO] error ejecutando %s",
            action_name,
        )

        dispatcher.utter_message(
            text="⚠️ No fue posible procesar la consulta académica."
        )

        return []


#================================================================

# 🧠 ACCIONES ACADÉMICAS

# ================================================================
class ActionVerEstadoEstudiante(Action):

    def name(self) -> str: return "action_ver_estado_estudiante"

    def run(self, dispatcher, tracker, domain):

        auth = validar_autenticacion(
            tracker,
            "estado_estudiante",
        )

        if auth:
            return auth

        return _exec(
            "estado_estudiante",
            dispatcher,
            tracker,
        )

class ActionTutorAsignado(Action):

    def name(self) -> str: return "action_tutor_asignado"

    def run(self, dispatcher, tracker, domain):

        auth = validar_autenticacion(
            tracker,
            "tutor_asignado",
        )

        if auth:
            return auth

        return _exec(
            "tutor_asignado",
            dispatcher,
            tracker,
    
        )


class ActionConsultarHorariosClases(Action):

    def name(self) -> str: return "action_consultar_horarios_clases"

    def run(self, dispatcher, tracker, domain):

        auth = validar_autenticacion(
            tracker,
            "horarios",
        )

        if auth:
            return auth

        return _exec(
            "horarios",
            dispatcher,
            tracker,
        )

class ActionConsultarProgresoCurso(Action):

    def name(self) -> str: return "action_consultar_progreso_curso"

    def run(self, dispatcher, tracker, domain):

        auth = validar_autenticacion(
           tracker,
           "progreso",
        )

        if auth:
            return auth

        return _exec(
            "progreso",
            dispatcher,
            tracker,
        )

class ActionHistorialAcademico(Action):

    def name(self) -> str:

        return "action_historial_academico"

    def run(
        self,
        dispatcher,
        tracker,
        domain,
    ):

        auth = validar_autenticacion(
            tracker,
            "historial_academico",
        )

        if auth:
            return auth

        return _exec(
            "historial_academico",
            dispatcher,
            tracker,
        )

class ActionAprenderTema(Action):

    def name(self):
        return "action_aprender_tema"

    def run(self, dispatcher, tracker, domain):
        pregunta = tracker.latest_message.get("text") or ""
        materia = detectar_materia(pregunta)
        rol = MATERIAS.get(materia.lower(), "Tutor Académico General")

        return [
            ActiveLoop(None),                
            SlotSet("requested_slot", None),
            SlotSet("requires_auth", False),      
            SlotSet("pending_action", None),      
            SlotSet("tema_consulta", pregunta),
            SlotSet("materia_detectada", materia),
            SlotSet("rol_academico", rol),
            SlotSet("auth_form", None)
        ]
