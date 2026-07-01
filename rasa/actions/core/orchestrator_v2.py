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
        """
        Construye únicamente el contexto realmente útil para el
        backend y el LLM.
        """

        text = (tracker.latest_message or {}).get("text", "")

        clean_text = normalize_text(text)

        intent = self.detect_intent(tracker)

        # --------------------------------------------------------
        # Detectar materia únicamente cuando aporta valor
        # --------------------------------------------------------

        if intent in LOW_RISK_INTENTS:
            materia = "tema academico"
        else:
            materia = detectar_materia(text)

        # --------------------------------------------------------
        # Slots relevantes
        # --------------------------------------------------------

        important_slots = {
            "materia": tracker.get_slot("materia"),
            "rol": tracker.get_slot("rol"),
            "autenticado": tracker.get_slot("autenticado"),
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
            "text": text,
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
        Decide cuál será el flujo de procesamiento.
        """

        intent = self.detect_intent(tracker)

        # --------------------------------------------------------
        # ACTIONS
        # --------------------------------------------------------

        if intent in ACTION_INTENTS:

            context = self.build_context(tracker)

            return {
                "type": "action",
                "action": ACTION_INTENTS[intent],
                "context": context,
            }

        # --------------------------------------------------------
        # A partir de aquí sí necesitamos contexto
        # --------------------------------------------------------

        context = self.build_context(tracker)

        self.logger.info(
            "[ORCHESTRATOR_V2] intent=%s user=%s materia=%s",
            intent,
            context["user"],
            context["materia"],
        )

        # --------------------------------------------------------
        # BACKEND
        # --------------------------------------------------------

        if intent in DATA_INTENTS:
            return {
                "type": "backend",
                "intent": intent,
                "context": context,
            }

        # --------------------------------------------------------
        # LLM
        # --------------------------------------------------------

        if intent in LOW_RISK_INTENTS:
            return {
                "type": "llm",
                "prompt": context["text"],
                "context": context,
            }

        # --------------------------------------------------------
        # DEFAULT
        # --------------------------------------------------------

        return {
            "type": "llm",
            "prompt": context["text"],
            "context": context,
        }