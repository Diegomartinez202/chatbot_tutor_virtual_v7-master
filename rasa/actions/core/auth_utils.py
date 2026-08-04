import os
import logging
from rasa_sdk.events import (
    SlotSet,
    FollowupAction,
)
from actions.runtime.action_handler import action_handler
logger = logging.getLogger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# ================================================================
# 🚀 BOOTSTRAP SAFE
# ================================================================

try:
    if not action_handler.registry:
        action_handler.bootstrap()
except Exception:
    logger.exception("[CORE] Error bootstrap ActionHandler")

def validar_autenticacion(
    tracker,
    pending_action: str,
    llm_request: dict,
):

    # ==========================================================
    # MODO DEMOSTRACIÓN
    # Permite ejecutar únicamente la consulta de certificados
    # sin autenticación para demostrar el flujo completo del bot.
    # En producción DEMO_MODE debe permanecer en False.
    # ==========================================================
    if DEMO_MODE and pending_action == "certificados":
        logger.info(
            "[AUTH] DEMO_MODE activo - omitiendo autenticación para certificados."
        )
        return None
   
    logger.warning("=" * 80)
    logger.warning("[TUTOR] Entró nuevamente")
    logger.warning(
        "authenticated=%s",
        tracker.get_slot("is_authenticated"),
    )
    logger.warning(
        "pending=%s",
        tracker.get_slot("pending_action"),
    )
    logger.warning(
        "llm_request=%s",
        tracker.get_slot("llm_request"),
    )
    logger.warning("=" * 80)
    
    
    if tracker.get_slot("is_authenticated"):
        return None

    logger.warning(
        "[AUTH] Solicitando login para %s",
        pending_action,
    )
    
    return [

        SlotSet(
            "proceso_activo",
            pending_action,
        ),

        SlotSet(
            "pending_action",
            pending_action,
        ),

       
        SlotSet(
            "llm_request",
            llm_request,
        ),

        FollowupAction(
            "action_solicitar_login",
        ),

    ]


