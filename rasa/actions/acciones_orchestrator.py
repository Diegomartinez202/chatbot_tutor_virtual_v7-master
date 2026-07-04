# ruta: rasa/actions/acciones_orchestrator.py

from __future__ import annotations

from typing import List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    EventType,
    FollowupAction,
    SlotSet,
)
from rasa_sdk.types import DomainDict

from .core.llm_engine import run_llm
from .core.orchestrator_v2 import OrchestratorV2
from .runtime.action_handler import action_handler
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
                "[ORCHESTRATOR] Decisión vacía."
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

        if decision.get("type") == "action":

            logger.info(
                "[ORCHESTRATOR] Ejecutando acción '%s'",
                decision.get("action"),
            )

            return [
                FollowupAction(
                    decision["action"]
                )
            ]

        # --------------------------------------------------------
        # 🌐 BACKEND ROUTING
        # --------------------------------------------------------

        if decision.get("type") == "backend":

            backend = decision.get("backend")

            logger.info(
                "[ORCHESTRATOR] Backend '%s'",
                backend,
            )

            action_handler.bootstrap()

            if not action_handler.exists(backend):

                logger.error(
                    "[ORCHESTRATOR] Backend '%s' no registrado.",
                    backend,
                )

                dispatcher.utter_message(
                    text="⚠️ El servicio solicitado no está disponible."
                )

                return []

            action_handler.execute(
                action_name=backend,
                dispatcher=dispatcher,
                tracker=tracker,
                payload=decision.get("context", {}),
            )

            return []

        # --------------------------------------------------------
        # 🧠 LLM ROUTING
        # --------------------------------------------------------

        if decision.get("type") == "llm":

            llm_context = decision.get(
                "context",
                {},
            )

            if not isinstance(
                llm_context,
                dict,
            ):
                llm_context = {}

            llm_context.setdefault(
                "flujo",
                "orchestrator",
            )

            answer = run_llm(
                prompt=decision["prompt"],
                tracker=tracker,
                context=llm_context,
                fallback=(
                    "No pude generar respuesta "
                    "en este momento."
                ),
            )

            clean_answer = answer.strip()

            if clean_answer.upper().startswith(
                "RESPUESTA:"
            ):
                clean_answer = clean_answer[
                    len("RESPUESTA:")
                :].strip()

            dispatcher.utter_message(
                text=clean_answer
            )

            return [
                SlotSet(
                    "pending_action",
                    None,
                ),
                SlotSet(
                    "requires_auth",
                    False,
                ),
                FollowupAction(
                    "action_ofrecer_continuar_tema"
                ),
            ]

        # --------------------------------------------------------
        # ⚠️ Tipo desconocido
        # --------------------------------------------------------

        logger.warning(
            "[ORCHESTRATOR] Tipo no soportado: %s",
            decision.get("type"),
        )

        dispatcher.utter_message(
            text="No pude procesar tu solicitud."
        )

        return []