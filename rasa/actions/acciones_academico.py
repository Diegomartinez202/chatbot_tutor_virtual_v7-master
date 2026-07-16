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
from .core.materias import MATERIAS
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

    if tracker.get_slot("is_authenticated"):
        return None

    return [

        SlotSet(
            "llm_request",
            {
                "instruction": (
                    "Explica al estudiante que necesita autenticarse "
                    "antes de consultar información personal."
                ),

                "context": {
                    "flujo": "auth_required",
                    "pending_action": pending_action,
                },

                "fallback": (
                    "Debes iniciar sesión para continuar."
                ),
          
                 "next_action": None,
            },
        ),

        FollowupAction(
            "action_handle_with_llm",
        ),

    ]

# ================================================================
# CATÁLOGO CENTRAL DE ACCIONES ACADÉMICAS
# ================================================================

ACCIONES_ACADEMICAS = {

    "estado_estudiante": {
        "backend": "estado_estudiante",
        "requires_auth": True,
    },

    "tutor_asignado": {
        "backend": "tutor_asignado",
        "requires_auth": True,
    },

    "horarios": {
        "backend": "horarios",
        "requires_auth": True,
    },

    "progreso": {
        "backend": "progreso",
        "requires_auth": True,
    },

    "historial": {
        "backend": "historial",
        "requires_auth": True,
    },

    "certificados": {
        "backend": "certificados",
        "requires_auth": True,
    },

    # --------------------------------------------------------
    # NUEVAS ACCIONES
    # --------------------------------------------------------

    "pagos": {
        "backend": "pagos",
        "requires_auth": True,
    },

    "notas": {
        "backend": "notas",
        "requires_auth": True,
    },

    "ficha": {
        "backend": "ficha",
        "requires_auth": True,
    },

    "inscripciones": {
        "backend": "inscripciones",
        "requires_auth": True,
    },

    # --------------------------------------------------------
    # Pública
    # --------------------------------------------------------

    "aprender_tema": {
        "backend": None,
        "requires_auth": False,
    },

}
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

def ejecutar_accion_academica(
    accion: str,
    dispatcher,
    tracker,
):

    config = ACCIONES_ACADEMICAS.get(accion)

    if not config:

        dispatcher.utter_message(
            text="La acción académica no está registrada."
        )

        return []

    if config["requires_auth"]:

        auth = validar_autenticacion(
            tracker,
            accion,
        )

        if auth:
            return auth

    backend = config["backend"]

    if backend is None:
        return []

    return _exec(
        backend,
        dispatcher,
        tracker,
    )
#================================================================

# 🧠 ACCIONES ACADÉMICAS

# ================================================================
class ActionVerEstadoEstudiante(Action):

    def name(self):
        return "action_ver_estado_estudiante"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_academica(
            "estado_estudiante",
            dispatcher,
            tracker,
        )

class ActionTutorAsignado(Action):

    def name(self):
        return "action_tutor_asignado"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_academica(
            "tutor_asignado",
            dispatcher,
            tracker,
        )

class ActionConsultarHorariosClases(Action):

    def name(self):
        return "action_consultar_horarios_clases"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_academica(
            "horarios",
            dispatcher,
            tracker,
        )
class ActionHistorialAcademico(Action):

    def name(self) -> str:
        return "action_historial_academico"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_academica(
            "historial",
            dispatcher,
            tracker,
        )

class ActionConsultarProgresoCurso(Action):

    def name(self):
        return "action_consultar_progreso_curso"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_academica(
            "progreso",
            dispatcher,
            tracker,
        )

class ActionConsultarCertificados(Action):

    def name(self):
        return "action_consultar_certificados"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_academica(
            "certificados",
            dispatcher,
            tracker,
        )

class ActionConsultarPagos(Action):

    def name(self) -> str:
        return "action_consultar_pagos"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_academica(
            "pagos",
            dispatcher,
            tracker,
        )

class ActionConsultarNotas(Action):

    def name(self) -> str:
        return "action_consultar_notas"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_academica(
            "notas",
            dispatcher,
            tracker,
        )
class ActionConsultarFicha(Action):

    def name(self) -> str:
        return "action_consultar_ficha"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_academica(
            "ficha",
            dispatcher,
            tracker,
        )

class ActionConsultarInscripciones(Action):

    def name(self) -> str:
        return "action_consultar_inscripciones"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_academica(
            "inscripciones",
            dispatcher,
            tracker,
        )
class ActionAprenderTema(Action):

    def name(self):
        return "action_aprender_tema"

    def run(self, dispatcher, tracker, domain):
        logger.info("=" * 80)
        logger.info("[ACADEMICO] ActionAprenderTema EJECUTADA")
        logger.info("texto=%s", tracker.latest_message.get("text"))
        logger.info("intent=%s", tracker.get_intent_of_latest_message())
        logger.info("=" * 80)
        
        logger.warning(
        "[TRACE][ActionAprenderTema] llm_request al entrar=%s",
        tracker.get_slot("llm_request"),
        )
        
        pregunta = tracker.latest_message.get("text") or ""

        materia = detectar_materia(pregunta)

        rol = MATERIAS.get(
            materia.lower(),
            "Tutor Académico General"
        )

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet("proceso_activo", "aprender_tema"),

            SlotSet("tema_consulta", pregunta),

            SlotSet("materia_detectada", materia),

            SlotSet("rol_academico", rol),

            SlotSet("auth_login_form", None),

        ]
        # ====================================================
        # COMPATIBILIDAD CON EL FLUJO LLM ANTERIOR
        # (antes estaba en ActionExplicarTemaLLM)
        # ====================================================

        if tracker.get_intent_of_latest_message() != "continuar_tema_si":

            eventos.append(
                SlotSet("tema_actual", pregunta)
            )

        # ====================================================
        # ENVIAR LA CONSULTA AL PIPELINE LLM
        # ====================================================

        eventos.append(
            FollowupAction("action_handle_with_llm")
        )
        logger.info(
            "[ACADEMICO] llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.info("Eventos que retorna ActionAprenderTema:")
        for e in eventos:
            logger.info("  %s", e)
        return eventos