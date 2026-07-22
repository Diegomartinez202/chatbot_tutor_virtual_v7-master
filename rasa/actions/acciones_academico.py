# ruta: rasa/actions/acciones_academico.py
from __future__ import annotations
import os
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
from .core.nlp_utils import detectar_materia, build_llm_request
from .core.materias import MATERIAS
logger = logging.getLogger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# ================================================================
# 🚀 BOOTSTRAP SAFE
# ================================================================

try:
    if not action_handler.registry:
        action_handler.bootstrap()
except Exception:
    logger.exception("[ACADEMICO] error bootstrap ActionHandler")


def validar_autenticacion(
    tracker,
    pending_action: str,
):

    # ==========================================================
    # MODO DEMOSTRACIÓN
    # Permite ejecutar únicamente la consulta de certificados
    # sin autenticación para demostrar el flujo completo del bot.
    # En producción DEMO_MODE debe permanecer en False.
    # ==========================================================
    if DEMO_MODE and pending_action == "certificados":
        logger.info(
            "[AUTH] DEMO_MODE activo - omitiendo autenticación para certificados."
        )
        return None
   
    if tracker.get_slot("is_authenticated"):
        return None

    return [

        SlotSet(
            "proceso_activo",
            pending_action,
        ),

        SlotSet(
            "pending_action",
            pending_action,
        ),

        FollowupAction(
            "action_solicitar_login",
        ),

    ]

# ================================================================
# CATÁLOGO CENTRAL DE ACCIONES ACADÉMICAS
# ================================================================

ACCIONES_ACADEMICAS = {

    "estado_estudiante": {
        "backend": "estado_estudiante",
        "requires_auth": True,
        "proceso": "estado_estudiante",
        "resume_action": "action_ver_estado_estudiante",
    },

    "tutor_asignado": {
        "backend": "tutor_asignado",
        "requires_auth": True,
        "proceso": "tutor_asignado",
        "resume_action": "action_tutor_asignado",
    },

    "horarios": {
        "backend": "horarios",
        "requires_auth": True,
        "proceso": "consultar_horarios",
        "resume_action": "action_consultar_horarios_clases",
    },

    "progreso": {
        "backend": "progreso",
        "requires_auth": True,
        "proceso": "consultar_progreso",
         "resume_action": "action_consultar_progreso_curso",
    },

    "historial": {
        "backend": "historial",
        "requires_auth": True,
        "proceso": "historial_academico",
        "resume_action": "action_historial_academico",
    },

    "certificados": {
        "backend": "certificados",
        "requires_auth": True,
        "proceso": "certificados",
        "resume_action": "action_consultar_certificados",
    },

    # --------------------------------------------------------
    # NUEVAS ACCIONES
    # --------------------------------------------------------

    "pagos": {
        "backend": "pagos",
        "requires_auth": True,
        "proceso": "pagos",
        "resume_action": "action_consultar_pagos",
    },

    "notas": {
        "backend": "notas",
        "requires_auth": True,
        "proceso": "notas",
        "resume_action": "action_consultar_notas",
    },

    "ficha": {
        "backend": "ficha",
        "requires_auth": True,
        "proceso": "notas",
        "resume_action": "action_consultar_ficha",
    },

    "inscripciones": {
        "backend": "inscripciones",
        "requires_auth": True,
         "proceso": "inscripciones",
        "resume_action": "action_consultar_inscripciones",
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

    backend = config["backend"]
    proceso = config["proceso"]

    eventos: List[EventType] = []

    # ==========================================================
    # Acciones protegidas
    # ==========================================================

    if config["requires_auth"]:

        auth = validar_autenticacion(
            tracker,
            proceso,
        )

        if auth:
            return auth

        # ------------------------------------------------------
        # Ya autenticado.
        # Registrar el proceso para reutilizar el pipeline
        # de cierre, encuestas y reinicio.
        # ------------------------------------------------------

        eventos.append(

            SlotSet(
                "proceso_activo",
                proceso,
            )

        )

        eventos.append(

            SlotSet(
                "pending_action",
                None,
            )

        )

    else:

        # ------------------------------------------------------
        # Flujo público
        # ------------------------------------------------------

        eventos.append(

            SlotSet(
                "proceso_activo",
                proceso,
            )

        )

    # ==========================================================
    # ACCIONES SIN BACKEND
    # ==========================================================

    if backend is None:
        return eventos

    # ==========================================================
    # EJECUTAR BACKEND
    # ==========================================================

    resultado = _exec(
        backend,
        dispatcher,
        tracker,
    )

    return eventos + resultado
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

        
        intent = tracker.get_intent_of_latest_message()

        if intent == "continuar_tema_si":

           tema = tracker.get_slot("tema_actual")
           llm_request = tracker.get_slot("llm_request")
           pending = tracker.get_slot("pending_action")

           if not any([tema, llm_request, pending]):

               dispatcher.utter_message(
                   text="No hay un tema activo para continuar."
               )

               dispatcher.utter_message(
                   response="utter_fin_consulta_academica"
               )

               return []
        
        
        logger.warning(
            "[TRACE] esperando_tema=True"
        )
        
        logger.info("=" * 80)
        logger.info("[ACADEMICO] ActionAprenderTema EJECUTADA")
        logger.info("texto=%s", tracker.latest_message.get("text"))
        logger.info("intent=%s", tracker.get_intent_of_latest_message())
        logger.info("=" * 80)

        logger.warning(
            "[TRACE][ActionAprenderTema] llm_request al entrar=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning(
            "[DEBUG] latest_message=%s",
            tracker.latest_message,
        )
        
        pregunta = tracker.latest_message.get("text") or ""

        materia = detectar_materia(pregunta)

        rol = MATERIAS.get(
            materia.lower(),
            "Tutor Académico General",
        )

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet("proceso_activo", "aprender_tema"),

            SlotSet("tema_consulta", pregunta),

            SlotSet(
                "nivel_explicacion",
                "basico",
            ),

            SlotSet("materia_detectada", materia),

            SlotSet("rol_academico", rol),

            SlotSet("auth_login_form", None),

        ]

        # ====================================================
        # COMPATIBILIDAD CON EL FLUJO LLM ANTERIOR
        # ====================================================

        if intent != "continuar_tema_si":

            eventos.append(
                SlotSet("tema_actual", pregunta)
            )

        # ====================================================
        # CONSTRUIR LLM REQUEST
        # ====================================================

        request = build_llm_request(

            instruction=pregunta,

            macroflujo="academic",

            subflujo="aprender_tema",

            requires_auth=False,

            next_action="action_ofrecer_continuar_tema",

        )

        logger.info(
            "[ACADEMICO] llm_request construido=%s",
            request,
        )

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        # ====================================================
        # CONTINUAR HACIA EL LLM
        # ====================================================

        eventos.append(
            FollowupAction("action_handle_with_llm")
        )

        logger.info("Eventos que retorna ActionAprenderTema:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos