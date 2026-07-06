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
        "backend": None,
        "requires_auth": False,
        "module": "academico",
    },

    "saludo": {
        "llm": True,
    },

    "despedida": {
        "llm": True,
    },

    "agradecimiento": {
        "llm": True,
    },

    # ============================================================
    # ACCIONES DEL SISTEMA
    # ============================================================

    "login": {
        "action": "action_ingreso_zajuna",
        "requires_auth": False,
    },

    "reset_password": {
        "action": "action_reset_password",
        "requires_auth": False,
    },

    "recuperar_contrasena": {
        "action": "action_recuperar_contrasena",
        "requires_auth": False,
    },

    # ============================================================
    # ACCIONES ACADÉMICAS PROTEGIDAS
    # ============================================================

    "consultar_estado": {
        "action": "action_ver_estado_estudiante",
        "backend": "estado_estudiante",
        "requires_auth": True,
        "module": "academico",
    },

    "consultar_horarios": {
        "action": "action_consultar_horarios_clases",
        "backend": "horarios",
        "requires_auth": True,
        "module": "academico",
    },

    "consultar_progreso": {
        "action": "action_consultar_progreso_curso",
        "backend": "progreso",
        "requires_auth": True,
        "module": "academico",
    },

    "consultar_tutor": {
        "action": "action_tutor_asignado",
        "backend": "tutor_asignado",
        "requires_auth": True,
        "module": "academico",
    },

    "consultar_certificados": {
        "action": "action_consultar_certificados",
        "backend": "certificados",
        "requires_auth": True,
        "module": "academico",
    },

    # ============================================================
    # NUEVAS ACCIONES ACADÉMICAS
    # ============================================================

    "consultar_pagos": {
        "action": "action_consultar_pagos",
        "backend": "pagos",
        "requires_auth": True,
        "module": "academico",
    },

    "consultar_notas": {
        "action": "action_consultar_notas",
        "backend": "notas",
        "requires_auth": True,
        "module": "academico",
    },

    "consultar_ficha": {
        "action": "action_consultar_ficha",
        "backend": "ficha",
        "requires_auth": True,
        "module": "academico",
    },

    "consultar_inscripciones": {
        "action": "action_consultar_inscripciones",
        "backend": "inscripciones",
        "requires_auth": True,
        "module": "academico",
    },

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

        if config.get("llm", False):
            materia = "tema academico"
        else:
            materia = detectar_materia(text)

        # --------------------------------------------------------
        # Slots relevantes
        # --------------------------------------------------------

        important_slots = {
            "materia": tracker.get_slot("materia"),
            "rol": tracker.get_slot("rol"),
            "is_authenticated": tracker.get_slot("is_authenticated"),
            "curso": tracker.get_slot("curso"),
            "programa": tracker.get_slot("programa"),
            "ficha": tracker.get_slot("ficha"),
        }

        # eliminar slots vacíos

        important_slots = {
            key: value
            for key, value in important_slots.items()
            if value not in (None, "", [], {})
        }

        return {
            "text": clean_text,
            "clean_text": clean_text,
            "materia": materia,
            "user": tracker.sender_id,
            "slots": important_slots,
        }

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
        if config.get("action"):

            return {
                "type":"action",
                "action":config["action"],
                "context":context
            }
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
        "[ORCHESTRATOR_V2] intent=%s user=%s materia=%s",
        intent,
        context["user"],
        context["materia"],
    )

    return {
        "type": "llm",
        "prompt": context["text"],
        "context": context,
    }