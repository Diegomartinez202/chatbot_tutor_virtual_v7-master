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
from actions.core.nlp_utils import validar_autenticacion
from typing import Any, Dict, List, Optional, Text
from rasa_sdk.events import EventType
from .core.llm_engine import run_llm
from .core.nlp_utils import detectar_materia, build_llm_request
from .core.materias import MATERIAS
from .core.orchestrator_v2 import ACTION_CATALOG
logger = logging.getLogger(__name__)



# ================================================================
# CATÁLOGO CENTRAL DE ACCIONES ACADÉMICAS
# ================================================================

ACCIONES_ADMINISTRATIVAS = {

    "consultar_estado": {
        "backend": "estado_estudiante",
        "requires_auth": True,
        "proceso": "consultar_estado",
        "resume_action": "action_ver_estado_estudiante",
    },

    "consultar_tutor": {
        "backend": "tutor_asignado",
        "requires_auth": True,
        "proceso": "consultar_tutor",
        "resume_action": "action_tutor_asignado",
    },

    "consultar_horarios": {
        "backend": "horarios",
        "requires_auth": True,
        "proceso": "consultar_horarios",
        "resume_action": "action_consultar_horarios_clases",
    },

    "consultar_progreso": {
        "backend": "progreso",
        "requires_auth": True,
        "proceso": "consultar_progreso",
         "resume_action": "action_consultar_progreso_curso",
    },

    "consultar_historial": {
        "backend": "historial",
        "requires_auth": True,
        "proceso": "consultar_historial",
        "resume_action": "action_historial_academico",
    },

    "consultar_certificados": {
        "backend": "certificados",
        "requires_auth": True,
        "proceso": "consultar_certificados",
        "resume_action": "action_consultar_certificados",
    },

    # --------------------------------------------------------
    # NUEVAS ACCIONES
    # --------------------------------------------------------

    "consultar_pagos": {
        "backend": "pagos",
        "requires_auth": True,
        "proceso": "consultar_pagos",
        "resume_action": "action_consultar_pagos",
    },

    "consultar_notas": {
        "backend": "notas",
        "requires_auth": True,
        "proceso": "consultar_notas",
        "resume_action": "action_consultar_notas",
    },

    "consultar_ficha": {
        "backend": "ficha",
        "requires_auth": True,
        "proceso": "consultar_ficha",
        "resume_action": "action_consultar_ficha",
    },

    "consultar_inscripciones": {
        "backend": "inscripciones",
        "requires_auth": True,
        "proceso": "consultar_inscripciones",
        "resume_action": "action_consultar_inscripciones",
    },
}

    # --------------------------------------------------------
    # Pública
    # --------------------------------------------------------

ACCIONES_ACADEMICAS = {
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
        "[SOPORTE] execute=%s user=%s",
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
            "[SOPORTE] error ejecutando %s",
            action_name,
        )

        dispatcher.utter_message(
            text="⚠️ No fue posible procesar la consulta de soporte."
        )

        return []

def ejecutar_accion_administrativa(
    accion: str,
    dispatcher,
    tracker,
):

    logger.info(
        "[ADMINISTRATIVO] Inicio proceso=%s authenticated=%s pending=%s",
        accion,
        tracker.get_slot("is_authenticated"),
        tracker.get_slot("pending_action"),
    )
    
    config = ACCIONES_ADMINISTRATIVAS.get(accion)

    if not config:
        dispatcher.utter_message(
            text="La acción administrativa no está registrada."
        )
        return []

    backend = config.get("backend")
    proceso = config["proceso"]

    llm_config = ACTION_CATALOG.get(proceso)

    if not llm_config:
        logger.error(
            "[ADMINISTRATIVO] No existe ACTION_CATALOG[%s]",
            proceso,
        )
       
        return []

    macroflujo = llm_config["macroflujo"]
    subflujo = llm_config["subflujo"]
    requires_auth = llm_config["requires_auth"]

    eventos: List[EventType] = []

    # ==========================================================
    # Acciones protegidas
    # ==========================================================

    if requires_auth:

        llm_request = build_llm_request(
        instruction="",
        macroflujo=macroflujo,
        subflujo=subflujo,
        requires_auth=requires_auth,
        pending_action=proceso,
    )
        logger.warning(
            "[ADMINISTRATIVO] llm_request=%s",
            llm_request,
        )
        auth = validar_autenticacion(
            tracker,
            proceso,
            llm_request,
        )
        logger.warning(
            "[ADMINISTRATIVO] validar_autenticacion retornó=%s",
            auth,
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

    logger.info(
        "[ADMINISTRATIVO] Ejecutando backend=%s con proceso_activo=%s",
        proceso,
        backend,
    )
    
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

        
        logger.warning("=" * 80)
        logger.warning("[TUTOR] Entró nuevamente")
        logger.warning(
            "authenticated=%s",
            tracker.get_slot("is_authenticated"),
        )
        logger.warning(
            "pending=%s",
            tracker.get_slot("pending_action"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)
        
        return ejecutar_accion_administrativa(
            "consultar_estado",
            dispatcher,
            tracker,
        )
   
class ActionTutorAsignado(Action):

    def name(self):
        return "action_tutor_asignado"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_administrativa(
            "consultar_tutor",
            dispatcher,
            tracker,
        )

class ActionConsultarHorariosClases(Action):

    def name(self):
        return "action_consultar_horarios_clases"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_administrativa(
            "consultar_horarios",
            dispatcher,
            tracker,
        )
class ActionHistorialAcademico(Action):

    def name(self) -> str:
        return "action_historial_academico"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_administrativa(
            "consultar_historial",
            dispatcher,
            tracker,
        )

class ActionConsultarProgresoCurso(Action):

    def name(self):
        return "action_consultar_progreso_curso"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_administrativa(
            "consultar_progreso",
            dispatcher,
            tracker,
        )

class ActionConsultarCertificados(Action):

    def name(self):
        return "action_consultar_certificados"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_administrativa(
            "consultar_certificados",
            dispatcher,
            tracker,
        )

class ActionConsultarPagos(Action):

    def name(self) -> str:
        return "action_consultar_pagos"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_administrativa(
            "consultar_pagos",
            dispatcher,
            tracker,
        )

class ActionConsultarNotas(Action):

    def name(self) -> str:
        return "action_consultar_notas"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_administrativa(
            "consultar_notas",
            dispatcher,
            tracker,
        )
class ActionConsultarFicha(Action):

    def name(self) -> str:
        return "action_consultar_ficha"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_administrativa(
            "consultar_ficha",
            dispatcher,
            tracker,
        )

class ActionConsultarInscripciones(Action):

    def name(self) -> str:
        return "action_consultar_inscripciones"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_accion_administrativa(
            "consultar_inscripciones",
            dispatcher,
            tracker,
        )

class ActionAprenderTema(Action):

    def name(self):
        return "action_aprender_tema"


    def run(self, dispatcher, tracker, domain):

        
        intent = tracker.get_intent_of_latest_message()

       
        # ====================================================
        # PROTECCIÓN DE FLUJOS ACTIVOS
        # Evita que soporte sea tomado como académico
        # ====================================================

        proceso = tracker.get_slot(
            "proceso_activo"
        )

        logger.warning(
            "[ACADEMICO] proceso_activo actual=%s",
            proceso,
        )


        if proceso in [
            "pqrsd",
            "crear_caso",
            "hablar_asesor",
            "recuperar_contrasena",
        ]:

            logger.warning(
                "[ACADEMICO] Bloqueado. Flujo soporte activo=%s",
                proceso,
            )

            return []
        
        
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

        pregunta = (
            tracker.latest_message.get("text") or ""
        ).strip()

        if len(pregunta) < 2:

            dispatcher.utter_message(

                text=(
                    "No logré entender el tema. "
                    "¿Podrías escribirlo nuevamente?"
                )

            )

            return []


        materia = detectar_materia(pregunta)

        rol = MATERIAS.get(
            materia.lower(),
            "Tutor Académico General",
        )

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet("tema_consulta", pregunta),

            SlotSet(
                "nivel_explicacion",
                "basico",
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                 False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

            SlotSet("materia_detectada", materia),

            SlotSet("rol_academico", rol),

            SlotSet("auth_login_form", None),

        ]

        # ====================================================
        # SOLO CAMBIA A ACADÉMICO SI NO EXISTE OTRO FLUJO
        # ====================================================

        if proceso not in [
            "pqrsd",
            "crear_caso",
            "hablar_asesor",
            "recuperar_contrasena",
        ]:

            eventos.append(
                SlotSet(
                    "proceso_activo",
                    "aprender_tema",
                )
            )
       
        
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

        logger.warning("=" * 80)
        logger.warning("[LLM] REQUEST CONSTRUIDO")
        logger.warning("%s", request)
        logger.warning("=" * 80)

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