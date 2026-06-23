from __future__ import annotations

import logging
from typing import Callable, Dict, Any

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

# ================================================================
# 🌐 IMPORT HANDLERS (BACKEND REAL LAYER)
# ================================================================
from .handlers.certificados_handler import handler as certificados_handler
from .handlers.estado_estudiante_handler import handler as estado_estudiante_handler
from .handlers.tutor_handler import handler as tutor_handler
from .handlers.horarios_handler import handler as horarios_handler
from .handlers.progreso_handler import handler as progreso_handler
from .handlers.historial_academico_handler import handler as historial_academico_handler
logger = logging.getLogger(__name__)

Handler = Callable[[CollectingDispatcher, Tracker, Dict[str, Any]], Any]


class ActionRegistry:

    def __init__(self):
        self._registry: Dict[str, Handler] = {}

    # ------------------------------------------------------------
    # REGISTER SINGLE
    # ------------------------------------------------------------
    def register(self, name: str, handler: Handler) -> None:

        if name in self._registry:

            logger.warning(
                "[Registry] duplicated registration %s",
                name
            )

        self._registry[name] = handler

        logger.info(
            "[Registry] registered → %s",
            name
        )

    # ------------------------------------------------------------
    # GET HANDLER
    # ------------------------------------------------------------
    def get(self, name: str) -> Handler | None:
        return self._registry.get(name)
    def get_all(self) -> Dict[str, Handler]:
        return self._registry

    # ------------------------------------------------------------
    # LOAD ALL BACKEND HANDLERS (PRODUCTION BOOTSTRAP)
    # ------------------------------------------------------------
    def load(self) -> None:

        # ========================================================
        # 📊 ACADEMIC CORE
        # ========================================================
        self.register("estado_estudiante", estado_estudiante_handler)
        self.register("tutor_asignado", tutor_handler)
        self.register("progreso", progreso_handler)
        self.register("horarios", horarios_handler)
        self.register("historial_academico", historial_academico_handler
)
        # ========================================================
        # 📜 CERTIFICADOS
        # ========================================================
        self.register("certificados", certificados_handler)


        logger.info("[Registry] ✅ ALL BACKEND HANDLERS LOADED")


# ================================================================
# 🌍 SINGLETON GLOBAL
# ================================================================
action_registry = ActionRegistry()