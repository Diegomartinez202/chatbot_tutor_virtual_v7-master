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
from actions.core.nlp_utils import build_llm_request
logger = logging.getLogger(__name__)

from .acciones_academico import ACCIONES_ACADEMICAS
from .acciones_soporte import ACCIONES_SOPORTE
from .acciones_academico import ACCIONES_ADMINISTRATIVAS


RESUME_ACTIONS = {
    **{
        cfg["proceso"]: cfg["resume_action"]
        for cfg in ACCIONES_ACADEMICAS.values()
        if cfg.get("resume_action")
    },
    **{
        cfg["proceso"]: cfg["resume_action"]
        for cfg in ACCIONES_SOPORTE.values()
        if cfg.get("resume_action")
    },

    **{
        cfg["proceso"]: cfg["resume_action"]
        for cfg in ACCIONES_ADMINISTRATIVAS.values()
        if cfg.get("resume_action")
    },
}


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
                
                pending = tracker.get_slot("pending_action")

                events = [
                    SlotSet("is_authenticated", True),
                    SlotSet("auth_state", "active"),
                    SlotSet("password", None),
                    SlotSet("email", email), 
                    SlotSet("llm_request", None),
                ]

                logger.info(
                    "[AUTH] Login exitoso. pending=%s llm_request=%s",
                    tracker.get_slot("pending_action"),
                    tracker.get_slot("llm_request"),
                )

                if pending:

                    events.append(
                        FollowupAction("action_reanudar_pending_action")
                    )

                return events

            else:
                dispatcher.utter_message(text="❌ Credenciales incorrectas. Por favor, intenta de nuevo.")
                return [SlotSet("is_authenticated", False), SlotSet("email", None), SlotSet("password", None)]

        logger.info(
            f"[AUTH_ROUTER] user={tracker.sender_id} "
            f"intent={intent} authenticated={is_authenticated}"
        )

        protected_intents = {
                "ver_estado_estudiante": "action_ver_estado_estudiante",
                "consultar_certificados": "action_consultar_certificados",
                "consultar_progreso_curso": "action_consultar_progreso_curso",
                "ver_tutor_asignado": "action_tutor_asignado",
                "consultar_horarios_clases": "action_consultar_horarios_clases",
                "historial_academico": "action_historial_academico",

                "consultar_pagos": "action_consultar_pagos",
                "consultar_notas": "action_consultar_notas",
                "consultar_ficha": "action_consultar_ficha",
                "consultar_inscripciones": "action_consultar_inscripciones",

                "crear_caso": "action_iniciar_soporte",
                "hablar_asesor": "action_solicitar_humano",
                "contactar_tutor": "action_enviar_correo_tutor",
        }

        action_to_execute = protected_intents.get(intent)

        if not is_authenticated:
            return [

                SlotSet(

                    "llm_request",

                    build_llm_request(

                        instruction=(
                            "Explica al estudiante que primero debe autenticarse."
                        ),

                        macroflujo="auth",

                        subflujo="auth_required",

                        requires_auth=True,

                        pending_action=intent,

                        fallback="Debes iniciar sesión para continuar.",

                    ),

                ),

                FollowupAction(
                    "action_handle_with_llm"
                ),
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


class ActionSolicitarLogin(Action):

    def name(self):
        return "action_solicitar_login"

    def run(
        self,
        dispatcher,
        tracker,
        domain,
    ):
        logger.warning("=" * 80)
        logger.warning("[AUTH] llm_request ANTES de modificar")
        logger.warning("%s", tracker.get_slot("llm_request"))
        logger.warning("=" * 80)
        pending = tracker.get_slot("pending_action")
        logger.warning("=" * 80)
        logger.warning("[TRACE AUTH] llm_request AL ENTRAR A ActionSolicitarLogin")
        logger.warning("%s", tracker.get_slot("llm_request"))
        logger.warning("=" * 80)
        dispatcher.utter_message(
            response="utter_login_requerido"
        )

        instrucciones = {

            "consultar_certificados":
                (
                    "Explica que la consulta de certificados requiere autenticación institucional. "
                    "Indica que, una vez el estudiante inicie sesión mediante el sistema oficial "
                    "de Zajuna y se valide el token JWT, el chatbot consultará los certificados "
                    "autorizados y mostrará el resultado directamente en la conversación. "
                    "Aclara que en esta demostración únicamente se presenta el flujo de integración."
                ),

            "consultar_estado":
                (
                    "Explica que el estado académico requiere autenticación institucional. "
                    "Después de validar el token JWT el chatbot consultará la información "
                    "académica autorizada del estudiante."
                ),

            "consultar_tutor":
                (
                    "Explica que el tutor asignado únicamente puede consultarse después de "
                    "autenticarse en la plataforma institucional. "
                    "Una vez validado el token JWT el sistema recuperará la información del tutor."
                ),

            "consultar_horarios":
                (
                    "Explica que los horarios de clase son información protegida. "
                    "Después del proceso de autenticación el chatbot consultará y mostrará "
                    "los horarios autorizados del estudiante."
                ),

            "consultar_historial":
                (
                    "Explica que el historial académico requiere autenticación. "
                    "Después de validar la identidad mediante JWT el chatbot consultará "
                    "el historial académico correspondiente."
                ),

            "consultar_progreso":
                (
                    "Explica que el progreso del curso requiere autenticación institucional. "
                    "Una vez validado el token el sistema recuperará el avance académico."
                ),

            "crear_caso":
                (
                    "Explica que la creación de un caso de soporte requiere autenticación "
                    "para asociar correctamente la solicitud al estudiante. "
                    "Después del inicio de sesión se abrirá el formulario de soporte, "
                    "se registrará el ticket en la plataforma y posteriormente se mostrará "
                    "la confirmación del caso."
                ),

            "contactar_tutor":
                (
                    "Explica que para contactar al tutor primero debe validarse la identidad "
                    "del estudiante. Después del inicio de sesión el sistema consultará el tutor "
                    "asignado y permitirá generar la solicitud de contacto."
                ),

            "hablar_asesor":
                (
                    "Explica que antes de escalar la conversación a un asesor institucional "
                    "es necesario validar la identidad del estudiante mediante autenticación. "
                    "Después del inicio de sesión el sistema habilitará la transferencia al "
                    "canal de atención correspondiente."
                ),

        }

        instruction = instrucciones.get(

            pending,

            (
                "Explica que esta funcionalidad requiere autenticación institucional. "
                "Después del inicio de sesión y la validación del token JWT el chatbot "
                "continuará automáticamente con la operación solicitada."
            ),

        )

        logger.info(
            "[AUTH] Login requerido para %s",
            pending,
        )

        
        # ==========================================================
        # Conservar el llm_request original para no perder
        # macroflujo, subflujo y next_action.
        # ==========================================================

        request = (tracker.get_slot("llm_request") or {}).copy()

        request["flow"] = "auth"

        request["instruction"] = instruction

        request.setdefault("context", {})
        request["context"]["pending_action"] = pending

        request["fallback"] = (
            "Esta funcionalidad requiere autenticación institucional. "
            "Después del inicio de sesión el proceso continuará automáticamente."
        )
        request.setdefault(
            "next_action",
            "action_ofrecer_continuar_soporte",
        )

        logger.info(
            "[AUTH] llm_request preservado=%s",
            request,
        )        
        logger.warning("=" * 80)
        logger.warning("[AUTH] llm_request DESPUÉS de modificar")
        logger.warning("%s", request)
        logger.warning("=" * 80)
        return [

            SlotSet(
                "llm_request",
                request,
            ),

            FollowupAction(
                "action_handle_with_llm",
            ),

        ]
class ActionReanudarPendingAction(Action):

    def name(self) -> Text:
        return "action_reanudar_pending_action"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.warning("=" * 80)
        logger.warning("[REANUDAR] Entrando a ActionReanudarPendingAction")
        logger.warning(
            "authenticated=%s pending=%s llm_request=%s",
            tracker.get_slot("is_authenticated"),
            tracker.get_slot("pending_action"),
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)
        
        pending = tracker.get_slot("pending_action")

        logger.info(
            "[PENDING] Reanudando acción pendiente=%s",
            pending,
        )
        logger.info(
            "[REANUDAR] pending=%s authenticated=%s",
            pending,
            tracker.get_slot("is_authenticated"),
        )


        if not pending:

            logger.info(
                "[PENDING] No existe acción pendiente."
            )

            return []

        resume_action = RESUME_ACTIONS.get(pending)
       
        logger.info(
            "[REANUDAR] Ejecutando resume_action=%s",
            resume_action,
        )
        
        
        if not resume_action:

            logger.warning(
                "[PENDING] No existe resume_action para %s",
                pending,
            )

            dispatcher.utter_message(
                text="No fue posible reanudar la acción solicitada."
            )

            return [
                SlotSet("pending_action", None),
            ]

        logger.info(
            "[PENDING] Ejecutando %s",
            resume_action,
        )
        logger.warning(
            "[REANUDAR] Ejecutando resume_action=%s",
            resume_action,
        )


        return [

            SlotSet(
                "pending_action",
                None,
            ),

            FollowupAction(
                resume_action,
            ),

        ]