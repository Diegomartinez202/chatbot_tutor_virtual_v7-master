# ruta: rasa/actions/acciones_orchestrator.py
from __future__ import annotations

from typing import Any, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import EventType

from .core.llm_engine import run_llm
from .core.orchestrator_v2 import OrchestratorV2
from .runtime.api_client import get
from .utils_logging import get_logger

# CORRECCIÓN: Se elimina la doble inicialización que sobrescribía el logger 
# y rompía el aislamiento y formateo de los contenedores Docker.
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

        # Ejecución de la matriz lógica del enrutador (Cerebro)
        decision = orchestrator.route(tracker)

        logger.info("[ORCH_DECISION] %s", decision.get("type", "desconocido"))

        # --------------------------------------------------------
        # 🔐 ACTION ROUTING
        # --------------------------------------------------------
        if decision["type"] == "action":
            dispatcher.utter_message(text="Procesando solicitud segura...")
            return []

        # --------------------------------------------------------
        # 🌐 BACKEND ROUTING
        # --------------------------------------------------------
        if decision["type"] == "backend":
            response = get(
                tracker,
                decision["endpoint"],
                default={}
            )
            dispatcher.utter_message(text=str(response))
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
                fallback="No pude generar respuesta en este momento."
            )

            # MEJORA: Sanitización del payload de salida para remover prefijos estructurales del prompt
            # Evita que el aprendiz vea la etiqueta técnica "RESPUESTA:" en su interfaz de chat
            clean_answer = answer.strip()
            if clean_answer.upper().startswith("RESPUESTA:"):
                clean_answer = clean_answer[len("RESPUESTA:"):].strip()

            dispatcher.utter_message(text=clean_answer)
            return []

        dispatcher.utter_message(text="No pude procesar tu solicitud.")
        return []