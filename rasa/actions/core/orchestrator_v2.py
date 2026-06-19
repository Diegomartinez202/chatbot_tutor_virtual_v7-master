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


# ================================================================
# 🧠 ORCHESTRATOR V2 (DECISION MATRIX CORE)
# ================================================================
class OrchestratorV2:

    def __init__(self):
        self.logger = logger

    # ------------------------------------------------------------
    # 🔍 INTENT DETECTION
    # ------------------------------------------------------------
    def detect_intent(self, tracker: Tracker) -> str:
        """Extrae el nombre de la intención NLU detectada por Rasa Core."""
        return (
            (tracker.latest_message or {})
            .get("intent", {})
            .get("name", "unknown")
        )

    # ------------------------------------------------------------
    # 🧠 CONTEXT BUILDER
    # ------------------------------------------------------------
    def build_context(self, tracker: Tracker) -> dict[str, Any]:  # MEJORA: Tipado nativo dict

        text = (tracker.latest_message or {}).get("text", "")

        return {
            "text": text,
            "clean_text": normalize_text(text),
            "materia": detectar_materia(text),
            "user": tracker.sender_id,
            "slots": dict(tracker.slots),
        }

    # ------------------------------------------------------------
    # ⚖️ DECISION ENGINE
    # ------------------------------------------------------------
    def route(self, tracker: Tracker) -> dict[str, Any]:  # MEJORA: Tipado nativo dict
        """
        Determina la estrategia óptima de respuesta evaluando la criticidad 
        del intent y emitiendo un payload estructurado para la acción custom.
        """
        intent = self.detect_intent(tracker)
        context = self.build_context(tracker)

        # MEJORA: Uso de lazy formatting para optimizar la serialización de strings bajo carga masiva
        self.logger.info(
            "[ORCHESTRATOR_V2] intent=%s user=%s materia=%s",
            intent,
            context["user"],
            context["materia"]
        )

        # 1️⃣ HIGH RISK → AUTH FLOW / SECURITY / ACTIONS
        if intent in ACTION_INTENTS:
            return {
                "type": "action",
                "action": ACTION_INTENTS[intent],
                "context": context,
            }

        # 2️⃣ DATA INTENTS → BACKEND FIRST
        if intent in DATA_INTENTS:
            return {
                "type": "backend",
                "intent": intent,
               "context": context,
            }

        # 3️⃣ LOW RISK → LLM RESPONSE
        if intent in LOW_RISK_INTENTS:
            return {
                "type": "llm",
                "prompt": context["text"],
                "context": context,
            }

        # 4️⃣ DEFAULT → LLM fallback inteligente
        return {
            "type": "llm",
            "prompt": context["text"],
            "context": context,
        }
