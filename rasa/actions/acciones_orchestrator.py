# ruta: rasa/actions/acciones_orchestrator.py
from __future__ import annotations

from typing import Any, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import EventType, SlotSet, FollowupAction

from .core.llm_engine import run_llm
from .core.orchestrator_v2 import OrchestratorV2
from .runtime.api_client import get
from .utils_logging import get_logger


logger = get_logger(__name__)

orchestrator = OrchestratorV2()


class ActionOrchestratorEntry(Action):

    def name(self) -> str:
        return "action_orchestrator_entry"

def run(
    self,
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    domain: DomainDict,
) -> List[EventType]:

    # --------------------------------------------------------
    # 🧠 Obtener decisión del orquestador
    # --------------------------------------------------------

    decision = orchestrator.route(tracker)

    if not decision:

        logger.warning(
            "[ORCHESTRATOR] decisión vacía."
        )

        dispatcher.utter_message(
            text="No pude determinar cómo procesar tu solicitud."
        )

        return []

    logger.info(
        "[ORCHESTRATOR] type=%s action=%s backend=%s",
        decision.get("type"),
        decision.get("action"),
        decision.get("backend"),
    )

    # --------------------------------------------------------
    # 🔐 ACTION ROUTING
    # --------------------------------------------------------

    if decision["type"] == "action":

        logger.info(
            "[ORCHESTRATOR] Ejecutando acción %s",
            decision["action"],
        )

        return [
            FollowupAction(
                decision["action"]
            )
        ]

    # --------------------------------------------------------
    # 🌐 BACKEND ROUTING
    # --------------------------------------------------------

    if decision["type"] == "backend":

        response = get(
            tracker,
            decision["backend"],
            default={},
        )

        dispatcher.utter_message(
            text=str(response)
        )

        return []

    # --------------------------------------------------------
    # 🧠 LLM ROUTING
    # --------------------------------------------------------

    if decision["type"] == "llm":

        prompt = decision["prompt"]

        answer = run_llm(
            prompt=prompt,
            tracker=tracker,
            context=decision.get("context", {}),
            fallback="No pude generar respuesta en este momento.",
        )

        clean_answer = answer.strip()

        if clean_answer.upper().startswith("RESPUESTA:"):
            clean_answer = clean_answer[len("RESPUESTA:"):].strip()

        dispatcher.utter_message(
            text=clean_answer
        )

        return [
            SlotSet("pending_action", None),
            SlotSet("requires_auth", False),
            FollowupAction("action_ofrecer_continuar_tema"),
        ]

    # --------------------------------------------------------
    # ⚠️ Tipo desconocido
    # --------------------------------------------------------

    logger.warning(
        "[ORCHESTRATOR] tipo no soportado: %s",
        decision.get("type"),
    )

    return []