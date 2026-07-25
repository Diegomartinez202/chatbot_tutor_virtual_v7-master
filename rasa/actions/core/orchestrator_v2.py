# ruta: rasa/actions/core/orchestrator_v2.py

from __future__ import annotations

import logging
from typing import Any

from rasa_sdk import Tracker

from .nlp_utils import normalize_text, detectar_materia

logger = logging.getLogger(__name__)

# ================================================================
# 🧠 INTENT CATEGORIES
# ================================================================

LOW_RISK_INTENTS = {
    "saludo",
    "despedida",
    "agradecimiento",
}

ACTION_INTENTS = {
    "login": "action_ingreso_zajuna",
    "reset_password": "action_reset_password",
    "recuperar_contrasena": "action_recuperar_contrasena",
}

DATA_INTENTS = {
    "consultar_certificados",
    "consultar_estado",
    "consultar_progreso",
    "consultar_tutor",
    "consultar_horarios",
}

ACTION_CATALOG = {

    # ============================================================
    # ACCIONES PÚBLICAS
    # ============================================================

    "aprender_tema": {
        "action": "action_aprender_tema",
        "requires_auth": False,
        "macroflujo": "academic",
        "subflujo": "aprender_tema",
    },

    "saludo":{
        "llm":True,
        "requires_auth": False,
        "macroflujo":"general",
        "subflujo":"saludo",
    },

    "despedida": {
        "llm": True,
        "requires_auth": False,
        "macroflujo": "general",
        "subflujo": "despedida",
    },

    "agradecimiento": {
        "llm": True,
        "requires_auth": False,
        "macroflujo": "general",
        "subflujo": "agradecimiento",
    },

    # ============================================================
    # ACCIONES DEL SISTEMA
    # ============================================================

    "login": {
        "action": "action_ingreso_zajuna",
        "requires_auth": False,
        "macroflujo": "auth",
        "subflujo": "login",
    },

    "reset_password": {
        "action": "action_reset_password",
        "requires_auth": False,
        "macroflujo": "auth",
        "subflujo": "reset_password",
    },

    "recuperar_contrasena": {
        "action": "action_recuperar_contrasena",
        "requires_auth": False,
        "macroflujo": "auth",
        "subflujo": "recuperar_contrasena",
    },

    # ============================================================
    # ACCIONES ACADÉMICAS PROTEGIDAS
    # ============================================================

    "consultar_estado": {
        "action": "action_ver_estado_estudiante",
        "backend": "estado_estudiante",
        "requires_auth": True,
        "macroflujo": "administrative",
        "subflujo": "estado_estudiante",
    },

    "solicitar_soporte": {
        "action":"action_soporte_tecnico_llm",
        "requires_auth": True,
        "macroflujo":"support",
        "subflujo":"ticket",
    },

    "consultar_horarios": {
        "action": "action_consultar_horarios_clases",
        "backend": "horarios",
        "requires_auth": True,
        "macroflujo": "academic",
        "subflujo": "horarios",
    },

    "consultar_progreso": {
        "action": "action_consultar_progreso_curso",
        "backend": "progreso",
        "requires_auth": True,
        "macroflujo":"academic",
        "subflujo":"progreso",
    },

    "consultar_tutor": {
        "action": "action_tutor_asignado",
        "backend": "tutor_asignado",
        "requires_auth": True,
        "macroflujo":"academic",
        "subflujo":"tutor",
    },

    "consultar_certificados": {
        "action": "action_consultar_certificados",
        "backend": "certificados",
        "requires_auth": True,
        "macroflujo": "academic",
        "subflujo": "certificados",
    },

    # ============================================================
    # NUEVAS ACCIONES ACADÉMICAS
    # ============================================================

    "consultar_pagos": {
        "action": "action_consultar_pagos",
        "backend": "pagos",
        "requires_auth": True,
        "macroflujo": "academic",
        "subflujo": "pagos",
    },

    "consultar_notas": {
        "action": "action_consultar_notas",
        "backend": "notas",
        "requires_auth": True,
        "macroflujo": "academic",
        "subflujo": "notas",
    },

    "consultar_ficha": {
        "action": "action_consultar_ficha",
        "backend": "ficha",
        "requires_auth": True,
        "macroflujo": "administrative",
        "subflujo": "ficha",
    },

    "consultar_inscripciones": {
        "action": "action_consultar_inscripciones",
        "backend": "inscripciones",
        "requires_auth": True,
        "macroflujo": "administrative",
        "subflujo": "inscripciones",
    },

    "hablar_asesor":{
       "action":"action_escalar_humano",
       "requires_auth": True,
       "macroflujo":"support",
       "subflujo":"asesor",
    },

    "contactar_tutor":{
       "action":"action_enviar_correo_tutor",
       "requires_auth": True,
       "macroflujo":"support",
       "subflujo":"correo",
    },

    "pqrs":{
       "action":"action_pqrs_llm",
       "requires_auth": False,
       "macroflujo":"support",
       "subflujo":"pqrs",
    },

    "preguntas_frecuentes":{

       "action":"action_preguntas_frecuentes_llm",
       "requires_auth": False,
       "macroflujo":"support",
       "subflujo":"faq",
    },

    "consultar_historial":{
       "action":"action_historial_academico",
       "backend":"historial",
       "requires_auth":True,
       "macroflujo":"administrative",
       "subflujo":"historial",
    }

}
# ================================================================
# 🧠 ORCHESTRATOR V2
# ================================================================

class OrchestratorV2:

    def __init__(self):
        self.logger = logger

    # ------------------------------------------------------------
    # 🔍 INTENT DETECTION
    # ------------------------------------------------------------

    def detect_intent(self, tracker: Tracker) -> str:
        """
        Obtiene el intent detectado por Rasa.
        """

        return (
            (tracker.latest_message or {})
            .get("intent", {})
            .get("name", "unknown")
        )

    # ------------------------------------------------------------
    # 🧠 CONTEXT BUILDER
    # ------------------------------------------------------------

    def build_context(self, tracker: Tracker) -> dict[str, Any]:
       
        text = (tracker.latest_message or {}).get("text", "").strip()

        clean_text = normalize_text(text)

        intent = self.detect_intent(tracker)

        # --------------------------------------------------------
        # Detectar materia únicamente cuando aporta valor
        # --------------------------------------------------------

        config = ACTION_CATALOG.get(intent, {})

        macroflujo = config.get(
            "macroflujo",
            "general",
        )

        subflujo = config.get(
            "subflujo",
            intent,
        )

        context = {

            "text": clean_text,
            "user": tracker.sender_id,
            "macroflujo": macroflujo,
            "subflujo": subflujo,
        }

        if macroflujo == "academic":
            materia = detectar_materia(text)
            context["materia"] = materia
            context["rol"] = tracker.get_slot(
                "rol_academico"
            )
            context["tema_consulta"] = tracker.get_slot(
                "tema_consulta"
            )
            context["nivel_explicacion"] = tracker.get_slot(
                "nivel_explicacion"
)

        elif macroflujo == "support":
            context["ticket"] = tracker.get_slot(
                "ticket_id"
            )

            context["proceso"] = tracker.get_slot(
                "proceso_activo"
            )

        elif macroflujo == "administrative":
            context["programa"] = tracker.get_slot(
                "programa"
            )

            context["ficha"] = tracker.get_slot(
                "ficha"
            )

            context["estado"] = tracker.get_slot(
                "estado_estudiante"
            )

        elif macroflujo == "auth":

            context["auth_state"] = tracker.get_slot(
                "auth_state"
            )

            context["is_authenticated"] = tracker.get_slot(
                "is_authenticated"
            )

        return context
    # ------------------------------------------------------------
    # ⚖️ DECISION ENGINE
    # ------------------------------------------------------------

    def route(self, tracker: Tracker) -> dict[str, Any]:
        """
        Decide cuál será el flujo de procesamiento utilizando el
        catálogo central de acciones.
        """

        intent = self.detect_intent(tracker)

        context = self.build_context(tracker)

        config = ACTION_CATALOG.get(intent)

        # --------------------------------------------------------
        # Intent registrado en el catálogo
        # --------------------------------------------------------

        if config:

            self.logger.info(
                "[ACTION_CATALOG] intent=%s config=%s",
                intent,
                config,
            )

            # ----------------------------------------------------
            # Acción Rasa
            # ----------------------------------------------------

            if config.get("action"):

                return {
                    "type": "action",
                    "action": config["action"],
                    "context": context,
                }

            # ----------------------------------------------------
            # Backend
            # ----------------------------------------------------

            if config.get("backend"):

                return {
                    "type": "backend",
                    "intent": config["backend"],
                    "context": context,
                }

            # ----------------------------------------------------
            # LLM
            # ----------------------------------------------------

            if config.get("llm"):

                return {
                    "type": "llm",
                    "prompt": context["text"],
                    "context": context,
                }

        # --------------------------------------------------------
        # Compatibilidad temporal mientras migran todos los intents
        # --------------------------------------------------------

        self.logger.info(

                 "[ORCHESTRATOR_V2] intent=%s macro=%s sub=%s",

                 intent,

                 context.get("macroflujo"),

                 context.get("subflujo"),

           )

        return {
            "type": "llm",
            "prompt": context["text"],
            "context": context,
        }