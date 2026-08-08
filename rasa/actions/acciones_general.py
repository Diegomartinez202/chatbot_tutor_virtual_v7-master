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
from .core.nlp_utils import build_llm_request
from rasa_sdk.events import Text, FollowupAction
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
        dispatcher,
        tracker,
        domain,
    ):

        logger.warning(
            "[CONTINUAR] proceso=%s tema=%s llm=%s",
            tracker.get_slot("proceso_activo"),
            tracker.get_slot("tema_actual"),
            tracker.get_slot("llm_request"),
)

        dispatcher.utter_message(
            response="utter_ofrecer_continuar"
        )

        esperando = tracker.get_slot(
            "esperando_decision_post_resolucion"
        )

        logger.warning(
            "[CONTINUAR_TEMA] esperando_decision_post_resolucion=%s",
            esperando,
        )

        if esperando:
            logger.warning(
                "[CONTINUAR_TEMA] Manteniendo espera post resolución"
            )

            return []


        logger.warning(
            "[CONTINUAR_TEMA] Flujo académico normal"
        )

        return [
            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "proceso_activo",
                "aprender_tema",
            ),

            SlotSet("confirmacion_cierre", "pendiente")
    ]
       
class ActionSolicitarTema(Action):

    
    def name(self):
        return "action_solicitar_tema"

    def run(self, dispatcher, tracker, domain):
        logger.warning(
            "[TRACE][ActionSolicitarTema] llm_request al entrar=%s",
            tracker.get_slot("llm_request"),
        )
        logger.info(
            "[ACADEMICO] Activando esperando_tema"
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

# =====================================================================
# REANUDAR APRENDIZAJE DESPUÉS DE RESPONDER "NO" A LA RESOLUCIÓN
# =====================================================================

class ActionReanudarAprendizaje(Action):

    def name(self) -> Text:
        return "action_reanudar_aprendizaje"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        proceso = tracker.get_slot("proceso_activo")

        tema = (
            tracker.get_slot("tema_actual")
            or tracker.get_slot("tema_consulta")
        )

        logger.info(
            "[POST_RESOLUCION] Reanudando aprendizaje. proceso=%s tema=%s",
            proceso,
            tema,
        )

        request = build_llm_request(
            instruction=tema,
            macroflujo="academic",
            subflujo="aprender_tema",
            requires_auth=False,
            next_action="action_ofrecer_continuar_tema",
        )

        return [

            SlotSet(
                "llm_request",
                request,
            ),

            SlotSet(
                "tema_actual",
                tema,
            ),

            SlotSet(
                "tema_consulta",
                tema,
            ),

            SlotSet(
                "proceso_activo",
                proceso,
            ),

            SlotSet(
                "esperando_resolucion",
                False,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                True,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

            FollowupAction(
                "action_ofrecer_continuar_tema",
            ),

        ]

class ActionProcesarGuardarPostResolucion(Action):

    def name(self) -> Text:
        return "action_procesar_guardar_post_resolucion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        intent = tracker.get_intent_of_latest_message()

        logger.warning("=" * 80)
        logger.warning(
            "[POST_RESOLUCION_GUARDAR] Procesando transición. intent=%s",
            intent,
        )
        logger.warning(
            "[POST_RESOLUCION_GUARDAR] proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "[POST_RESOLUCION_GUARDAR] reanudar_pendiente=%s",
            tracker.get_slot("reanudar_pendiente"),
        )
        logger.warning(
            "[POST_RESOLUCION_GUARDAR] confirmacion_cierre=%s",
            tracker.get_slot("confirmacion_cierre"),
        )
        logger.warning("=" * 80)

        # =====================================================
        # NO -> cancelar cierre y volver al aprendizaje
        # =====================================================

        if intent == "deny":

            logger.info(
                "[POST_RESOLUCION_GUARDAR] NO -> reanudar aprendizaje"
            )

            return [
                SlotSet(
                    "reanudar_pendiente",
                    False,
                ),

                SlotSet(
                    "confirmacion_cierre",
                    None,
                ),
                SlotSet(
                    "esperando_decision_post_resolucion",
                    False,
                ),
                FollowupAction(
                    "action_ofrecer_continuar_tema"
                ),
            ]

        # =====================================================
        # SI -> continuar proceso normal de cierre
        # =====================================================

        if intent == "affirm":

            logger.info(
                "[POST_RESOLUCION_GUARDAR] SI -> continuar cierre"
            )

            return [
                SlotSet(
                    "reanudar_pendiente",
                    False,
                ),
                SlotSet(
                    "esperando_decision_post_resolucion",
                    False,
                ),

                SlotSet(
                    "confirmacion_cierre",
                    None,
                ),

                FollowupAction(
                    "action_decidir_cierre"
                ),
            ]

        logger.warning(
            "[POST_RESOLUCION_GUARDAR] Intent no esperado: %s",
            intent,
        )

        return []

