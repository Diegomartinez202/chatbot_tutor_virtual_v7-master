# ruta: rasa/actions/acciones_academico.py

from __future__ import annotations

import logging
from typing import Any, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import (
    SlotSet,
    FollowupAction,
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


def validar_autenticacion(dispatcher: CollectingDispatcher, tracker: Tracker) -> bool:

    if tracker.get_slot("is_authenticated") is not True:
        msg = (
            "🔒 **Acceso restringido**\n\n"
            "Para consultar esta información personal, debes estar autenticado.\n\n"
            "**Sigue estos pasos:**\n"
            "1. Ingresa a: https://localhost/login\n"
            "2. Inicia sesión con tus credenciales SENA/Zajuna.\n"
            "3. Regresa aquí y vuelve a realizar tu consulta."
        )
        dispatcher.utter_message(text=msg)
        return False
    return True

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


# ================================================================
# 🧠 ACCIONES ACADÉMICAS
# ================================================================

class ActionVerEstadoEstudiante(Action):
    def name(self) -> str: return "action_ver_estado_estudiante"

    def run(self, dispatcher, tracker, domain):
      
        if not validar_autenticacion(dispatcher, tracker):
            return [SlotSet("requires_auth", True)]
        return _exec("estado_estudiante", dispatcher, tracker)

class ActionTutorAsignado(Action):
    def name(self) -> str: return "action_tutor_asignado"

    def run(self, dispatcher, tracker, domain):
        if not validar_autenticacion(dispatcher, tracker):
            return [SlotSet("requires_auth", True)]
        return _exec("tutor_asignado", dispatcher, tracker)

class ActionConsultarHorariosClases(Action):
    def name(self) -> str: return "action_consultar_horarios_clases"

    def run(self, dispatcher, tracker, domain):
        if not validar_autenticacion(dispatcher, tracker):
            return [SlotSet("requires_auth", True)]
        return _exec("horarios", dispatcher, tracker)

class ActionConsultarProgresoCurso(Action):
    def name(self) -> str: return "action_consultar_progreso_curso"

    def run(self, dispatcher, tracker, domain):
        if not validar_autenticacion(dispatcher, tracker):
            return [SlotSet("requires_auth", True)]
        return _exec("progreso", dispatcher, tracker)
        
class ActionHistorialAcademico(Action):

    def name(self) -> str:
        return "action_historial_academico"

    def run(
        self,
        dispatcher,
        tracker,
        domain
    ):
        if not validar_autenticacion(dispatcher, tracker):
            # Retornamos el slot sin llamar al LLM
            return [SlotSet("requires_auth", True)]

        return _exec(
            "historial_academico",
            dispatcher,
            tracker
        )

class ActionAprenderTema(Action):

    def name(self):
        return "action_aprender_tema"

    def run(
        self,
        dispatcher,
        tracker,
        domain,
    ):

        pregunta = (
            tracker.latest_message.get("text")
            or ""
        )

        materia = detectar_materia(
            pregunta
        )

        rol = MATERIAS.get(
            materia.lower(),
            "Tutor Académico General"
        )

        return [

            SlotSet(
                "tema_consulta",
                pregunta
            ),

            SlotSet(
                "materia_detectada",
                materia
            ),

            SlotSet(
                "rol_academico",
                rol
            )
        ]
