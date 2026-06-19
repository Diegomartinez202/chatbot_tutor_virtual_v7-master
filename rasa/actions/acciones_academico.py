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

    def name(self) -> str:
        return "action_ver_estado_estudiante"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Any]:

        return _exec(
            "estado_estudiante",
            dispatcher,
            tracker,
        )


class ActionTutorAsignado(Action):

    def name(self) -> str:
        return "action_tutor_asignado"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Any]:

        return _exec(
            "tutor_asignado",
            dispatcher,
            tracker,
        )


class ActionConsultarHorariosClases(Action):

    def name(self) -> str:
        return "action_consultar_horarios_clases"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Any]:

        return _exec(
            "horarios",
            dispatcher,
            tracker,
        )


class ActionConsultarProgresoCurso(Action):

    def name(self) -> str:
        return "action_consultar_progreso_curso"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Any]:

        return _exec(
            "progreso",
            dispatcher,
            tracker,
        )

# ================================================================
# 🔁 LEGACY COMPATIBILITY
# ================================================================

def _legacy_wrapper(
    action_name: str,
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
) -> List[Any]:

    try:
        return _exec(
            action_name,
            dispatcher,
            tracker,
        )

    except Exception:
        logger.exception(
            "[ACADEMICO LEGACY] error %s",
            action_name,
        )

        dispatcher.utter_message(
            text="⚠️ No fue posible completar la operación."
        )

        return []
     


class ActionHistorialAcademico(Action):
    def name(self) -> Text:
        return "action_historial_academico"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        historial_raw = (
            tracker.get_slot("historial_academico")
            or ""
        ).strip()

        if not historial_raw:
            historial_raw = (
                tracker.latest_message.get("text")
                or ""
            ).strip()

        if not historial_raw:
            dispatcher.utter_message(
                text=(
                    "Puedes contarme brevemente tu historial académico: "
                    "qué has estudiado, en qué institución, "
                    "qué cursos o formaciones has realizado."
                )
            )
            return []

        events: List[EventType] = [
            SlotSet(
                "historial_academico",
                historial_raw,
            )
        ]

        fallback_text = (
            "Gracias por compartir tu historial académico 🙌.\n\n"
            "Con la experiencia que comentas, ya tienes una base importante "
            "para seguir avanzando en tu formación. "
            "Esa trayectoria te puede ayudar a comprender mejor los contenidos, "
            "participar con más seguridad en las actividades y aprovechar los "
            "cursos que ofrece el SENA / Zajuna.\n\n"
            "Si quieres, ahora podemos buscar cursos relacionados con tu perfil, "
            "revisar opciones de certificación o profundizar en algún tema "
            "específico que te interese."
        )

        prompt = (
            "Eres un tutor virtual del SENA.\n\n"
            "El estudiante describe su historial académico así:\n"
            f"\"{historial_raw}\"\n\n"
            "Genera una respuesta amable y motivadora donde:\n"
            "- Resumas en 1–2 frases el perfil académico del estudiante.\n"
            "- Le indiques cómo ese historial puede ayudarle en su proceso "
            "formativo en el SENA / Zajuna.\n"
            "- Le sugieras que puede seguir consultando cursos, "
            "certificaciones o temas específicos.\n\n"
            "Responde en español, máximo 2–3 párrafos, "
            "sin viñetas largas."
        )

        try:
            respuesta_llm = run_llm(
                prompt=prompt,
                tracker=tracker,
                fallback=fallback_text,
            )

        except Exception:
            logger.exception(
                "[LLM] Error en action_historial_academico"
            )
            respuesta_llm = fallback_text

        dispatcher.utter_message(
            text=respuesta_llm or fallback_text
        )

        return events

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
            ),

            FollowupAction(
                "action_handle_with_llm"
            )
        ]


class ActionZajunaGetEstadoEstudiante(Action):

    def name(self) -> str:
        return "zajuna_get_estado_estudiante"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Any]:

        return _legacy_wrapper(
            "estado_estudiante",
            dispatcher,
            tracker,
 )