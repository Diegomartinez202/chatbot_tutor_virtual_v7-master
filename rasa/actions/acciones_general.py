# ruta: rasa/actions/acciones_general.py

from __future__ import annotations

from typing import List, Dict, Any, Optional
import json
import logging

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import EventType
from rasa_sdk.events import SlotSet
from .common import (
    jlog,
    ACTIONS_PING_HELPDESK,
    HELPDESK_WEBHOOK,
    send_email,
    RESET_URL_BASE,
)

logger = logging.getLogger(__name__)


# ================================================================
# 📧 RECUPERACIÓN DE CORREO (PRODUCCIÓN SEGURA)
# ================================================================
class ActionEnviarCorreo(Action):

    def name(self) -> str:
        return "action_enviar_correo"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        email: Optional[str] = (tracker.get_slot("email") or "").strip()

        if not email:
            dispatcher.utter_message(
                text="⚠️ Necesito tu correo electrónico para continuar (ej: usuario@ejemplo.com)."
            )
            return []

        try:
            reset_link = f"{RESET_URL_BASE}/reset?email={email}"

            body = (
                "Hola,\n\n"
                "Has solicitado recuperar tu contraseña.\n\n"
                "Accede aquí: {reset_link}\n\n"
                "Si no fuiste tú, ignora este mensaje."
            )

            sent = send_email("Recuperación de contraseña", body, email)

            jlog(
                logging.INFO,
                "action_enviar_correo",
                email=email,
                sent=bool(sent),
            )

            dispatcher.utter_message(
                text=(
                    "📬 Te envié un enlace de recuperación a tu correo."
                    if sent
                    else "ℹ️ No pude enviar el correo ahora, pero tu solicitud fue registrada."
                )
            )

        except Exception as e:
            logger.exception(f"[EMAIL_ERROR] {e}")

            dispatcher.utter_message(
                text="⚠️ No pude procesar tu solicitud de recuperación en este momento."
            )

        return []


# ================================================================
# 🧑‍💻 CONEXIÓN A HUMANO (THIN ACTION)
# ================================================================
class ActionConectarHumano(Action):

    def name(self) -> str:
        return "action_conectar_humano"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info(f"[HANDOVER] Requesting human agent for user={tracker.sender_id}")

        dispatcher.utter_message(
            text="🧑‍💻 Te estoy conectando con un agente humano. Por favor espera un momento…"
        )

        return []


# ================================================================
# 🩺 HEALTHCHECK (SISTEMA + DEPENDENCIAS)
# ================================================================
class ActionHealthCheck(Action):

    def name(self) -> str:
        return "action_health_check"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        status: Dict[str, Any] = {
            "actions": "ok",
            "helpdesk": "unknown",
        }

        # --------------------------------------------------------
        # 🌐 CHECK HELP DESK (OPCIONAL)
        # --------------------------------------------------------
        if ACTIONS_PING_HELPDESK:
            try:
                import requests

                r = requests.options(HELPDESK_WEBHOOK, timeout=3)
                status["helpdesk"] = f"ok ({r.status_code})"

            except Exception as e:
                logger.warning(f"[HELPDESK_FAIL] {e}")
                status["helpdesk"] = "error"

        else:
            status["helpdesk"] = "disabled"

        dispatcher.utter_message(
            text=f"health: {json.dumps(status, ensure_ascii=False)}"
        )

        return []


# ================================================================
# 🔄 CONTINUIDAD DE FLUJO (ORCHESTRATOR FRIENDLY)
# ================================================================
class ActionOfrecerContinuarTema(Action):

    def name(self) -> str:
        return "action_ofrecer_continuar_tema"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        dispatcher.utter_message(response="utter_ofrecer_continuar")

        return []

class ActionSolicitarTema(Action):

    
    def name(self):
        return "action_solicitar_tema"
 

    def run(self, dispatcher, tracker, domain):
        logger.warning(
            "[TRACE][ActionSolicitarTema] llm_request al entrar=%s",
            tracker.get_slot("llm_request"),
        )
        dispatcher.utter_message(
            response="utter_solicitar_tema"
        )

        return [

            SlotSet("llm_request", None),

            SlotSet(
                "esperando_tema",
                True
            ),

            SlotSet(
                "proceso_activo",
                "aprender_tema"
            )

        ]