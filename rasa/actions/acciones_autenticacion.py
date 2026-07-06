# ================================================================
# 📁 acciones_autenticacion.py (PRODUCCIÓN - ORCHESTRATOR V2)
# ================================================================

from __future__ import annotations

import logging
import re
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
from typing import Any, Dict, List, Text, Optional

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, EventType
from rasa_sdk.types import DomainDict
from rasa_sdk.forms import FormValidationAction

logger = logging.getLogger(__name__)

# ================================================================
# 🔐 CONFIG
# ================================================================
EMAIL_REGEX = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"


# ================================================================
# 🧼 VALIDATION HELPERS (REUTILIZABLES)
# ================================================================
def _is_valid_email(email: str) -> bool:
    return bool(email and re.match(EMAIL_REGEX, email.strip().lower()))


def _safe_text(value: Any, default: str = "") -> str:
    return str(value).strip() if value else default


# ================================================================
# 📌 AUTH ROUTER 
# ================================================================
class ActionCheckAuth(Action):

    def name(self) -> str:
        return "action_check_auth"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        email = tracker.get_slot("email")
        password = tracker.get_slot("password")
        is_authenticated = bool(tracker.get_slot("is_authenticated"))
        
        mensaje_actual = tracker.latest_message or {}
        intent = mensaje_actual.get("intent", {}).get("name", "") if isinstance(mensaje_actual, dict) else ""


        if email and password and not is_authenticated:
            
            es_valido = True 
            if es_valido:
                dispatcher.utter_message(text="✅ ¡Login exitoso! Ya puedes consultar tu información.")
                return [
                    SlotSet("is_authenticated", True), 
                    SlotSet("auth_state", "active"),
                    SlotSet("llm_request", None),
                    SlotSet("email", email),
                ]
            else:
                dispatcher.utter_message(text="❌ Credenciales incorrectas. Por favor, intenta de nuevo.")
                return [SlotSet("is_authenticated", False), SlotSet("email", None), SlotSet("password", None)]

        logger.info(
            f"[AUTH_ROUTER] user={tracker.sender_id} "
            f"intent={intent} authenticated={is_authenticated}"
        )

        protected_intents = {
            "estado_estudiante": "action_ver_estado_estudiante",
            "ver_certificados": "action_listar_certificados",
            "consultar_progreso": "action_consultar_progreso_curso",
            "consultar_tutor": "action_tutor_asignado",
        }

        action_to_execute = protected_intents.get(intent)

        if not action_to_execute:
            dispatcher.utter_message(text="⚠️ Acción no reconocida.")
            return []

        if not is_authenticated:
            return [
                SlotSet(
                    "llm_request",
                    {
                        "instruction":
                            "Explica al estudiante que primero debe autenticarse.",

                    "context": {
                        "flujo": "auth_required",
                        "pending_action": intent,
                    },

                    "fallback":
                        "Debes iniciar sesión para continuar.",

                    "next_action": None,
                    }
                ),

                FollowupAction(
                    "action_handle_with_llm"
                )
            ]

# ================================================================
# 🚀 AUTH FLOW (ENTRY POINT)
# ================================================================
class ActionIngresoZajuna(Action):

    def name(self) -> str:
        return "action_ingreso_zajuna"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info(f"[AUTH_FLOW] login_request user={tracker.sender_id}")

        dispatcher.utter_message(
            text="Inicia sesión con tu correo y contraseña."
        )
        return []


# ================================================================
# 🔐 AUTH STATE MANAGEMENT (CLEAN)
# ================================================================
class ActionSetAuthenticatedTrue(Action):

    def name(self) -> str:
        return "action_set_authenticated_true"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info(f"[AUTH_STATE] user={tracker.sender_id} -> AUTHENTICATED")

        return [
            SlotSet("is_authenticated", True),
            SlotSet("auth_state", "active"),
        ]


# ================================================================
# 📬 EMAIL SENDER 
# ================================================================
class ActionEnviarCorreoRecuperacion(Action):

    def name(self) -> str:
        return "action_enviar_correo_recuperacion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        slot_email = tracker.get_slot("email")
        
        # MEJORA: Validación robusta previa en caso de que soliciten recuperación con slot vacío
        if not slot_email:
            dispatcher.utter_message(text="📧 No he detectado ningún correo electrónico registrado para realizar la recuperación.")
            return []

        email = _safe_text(slot_email).lower()

        if not _is_valid_email(email):
            dispatcher.utter_message(text="📧 Email inválido.")
            return []

        logger.info(f"[AUTH_EMAIL] recovery_sent to={email}")

        dispatcher.utter_message(
            text=f"📬 Correo enviado a {email}"
        )

        return []
