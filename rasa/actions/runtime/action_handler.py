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

    # -------------------------
    # REGISTER
    # -------------------------
    def register(self, name: str, handler: Any) -> None:
        self.registry[name] = handler
        logger.info(
            "[ActionHandler] registered → %s",
            name,
        )

    # -------------------------
    # RESOLVE
    # -------------------------
    def resolve(self, name: str) -> Optional[Any]:
        return self.registry.get(name)

    # -------------------------
    # BOOTSTRAP (SAFE)
    # -------------------------
    def bootstrap(self):

        if self._bootstrapped:
            return

        action_registry.load()

        for name, handler in action_registry.get_all().items():
            self.register(name, handler)

        self._bootstrapped = True

        logger.info(
            "[ActionHandler] 🚀 Bootstrap completed"
        )

    # -------------------------
    # EXECUTE
    # -------------------------
    def execute(
        self,
        action_name: str,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Any:

        payload = payload or {}

        handler = self.resolve(action_name)

        if not handler:
            dispatcher.utter_message(
                text="⚠️ Acción no disponible en el sistema."
            )
            return None

        try:
            return handler(dispatcher, tracker, payload)

        except Exception as e:
            logger.exception(
                "[ActionHandler] error %s -> %s",
                action_name,
                e,
            )

            dispatcher.utter_message(
                text="⚠️ Error interno ejecutando acción."
            )
            return None


# -------------------------
# SINGLETON
# -------------------------
action_handler = ActionHandler()