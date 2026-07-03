from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

from .registry import action_registry

logger = logging.getLogger(__name__)


class ActionHandler:

    def __init__(self):

        self.registry: Dict[str, Any] = {}
        self._bootstrapped = False

    # ---------------------------------------------------------
    # REGISTER
    # ---------------------------------------------------------

    def register(self, name: str, handler: Any) -> None:

        self.registry[name] = handler

        logger.info(
            "[ActionHandler] registered → %s",
            name,
        )

    # ---------------------------------------------------------
    # RESOLVE
    # ---------------------------------------------------------

    def resolve(self, name: str) -> Optional[Any]:

        return self.registry.get(name)

    # ---------------------------------------------------------
    # EXISTS
    # ---------------------------------------------------------

    def exists(self, action_name: str) -> bool:

        return action_name in self.registry

    # ---------------------------------------------------------
    # BOOTSTRAP (SAFE)
    # ---------------------------------------------------------

    def bootstrap(self) -> None:

        if self._bootstrapped:

            logger.info(
                "[ActionHandler] bootstrap omitido."
            )

            return

        action_registry.load()

        for name, handler in action_registry.get_all().items():

            self.register(name, handler)

        self._bootstrapped = True

        logger.info(
            "[ActionHandler] 🚀 Bootstrap completed"
        )

    # ---------------------------------------------------------
    # SAFE EXECUTION
    # ---------------------------------------------------------

    def execute_safe(
        self,
        handler: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        payload: Optional[Dict[str, Any]],
    ) -> Any:

        try:

            return handler(
                dispatcher,
                tracker,
                payload,
            )

        except Exception:

            logger.exception(
                "[ActionHandler] Error ejecutando handler."
            )

            dispatcher.utter_message(
                text="⚠️ Ocurrió un error interno."
            )

            return None

    # ---------------------------------------------------------
    # EXECUTE (INTERFAZ PÚBLICA)
    # ---------------------------------------------------------

    def execute(
        self,
        action_name: str,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Any:

        payload = payload or {}

        handler = self.resolve(action_name)

        if handler is None:

            logger.warning(
                "[ActionHandler] Acción '%s' no registrada.",
                action_name,
            )

            dispatcher.utter_message(
                text="⚠️ Acción no disponible en el sistema."
            )

            return None

        logger.info(
            "[ActionHandler] Ejecutando '%s'",
            action_name,
        )

        return self.execute_safe(
            handler=handler,
            dispatcher=dispatcher,
            tracker=tracker,
            payload=payload,
        )


# ---------------------------------------------------------
# SINGLETON
# ---------------------------------------------------------

action_handler = ActionHandler()