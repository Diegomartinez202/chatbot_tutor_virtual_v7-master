# ruta: rasa/actions/acciones_admin.py
from __future__ import annotations

import logging
from typing import List, Any, Dict

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType
from rasa_sdk.events import FollowupAction, ActiveLoop 
from rasa_sdk.events import Restarted

logger = logging.getLogger(__name__)


# ================================================================
# 🔄 REINICIO CONVERSACIÓN (PRODUCCIÓN)
# ================================================================

class ActionReiniciarConversacion(Action):

    def name(self) -> str:
        return "action_reiniciar_conversacion"

    def run(
        self, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[str, Any]
    ) -> List[EventType]:

        logger.info(f"[ADMIN] reset_conversation user={tracker.sender_id}")
        logger.warning("=" * 80)
        logger.warning("[RESTART] EJECUTANDO")
        logger.warning("=" * 80)

        dispatcher.utter_message(response="utter_reinicio_confirmado")

        logger.warning(
                "[RESTART] eventos antes=%s",
                len(tracker.events),
        )
        logger.info(
            "[RESTART] Solicitando Restarted() a Rasa."
        )
        return [

            Restarted(),
            SlotSet("session_activa", True),
            SlotSet("turnos_conversacion", 0),
            SlotSet("sesion_larga", False),
            SlotSet("proceso_activo", None),
            SlotSet("esperando_tema", False),
            SlotSet("continuando_tema", False),
            SlotSet("cambio_tema", False),
            SlotSet("tema_actual", None),
            SlotSet("tema_consulta", None),
            SlotSet("tema_anterior", None),
            SlotSet("historial_academico", None),
            SlotSet("materia_detectada", None),
            SlotSet("rol_academico", None),
            SlotSet("nivel_explicacion", None),
            SlotSet("nota", None),
            SlotSet("llm_request",None),
            SlotSet("ultima_respuesta_llm", None),
            SlotSet("ultima_interaccion", None),
            SlotSet("esperando_resolucion", False),
            SlotSet("esperando_decision_post_resolucion", False),
            SlotSet("problema_resuelto", None),
            SlotSet("confirmacion_cierre", None),
            SlotSet("encuesta_activa", False),       
            SlotSet("encuesta_incompleta", False), 
            SlotSet("esperando_encuesta_general", False),
            SlotSet("encuesta_tipo", None),
            SlotSet("nivel_satisfaccion", None),        
            SlotSet("calificacion_numerica", None),
            SlotSet("comentario", None),
            SlotSet("satisfaccion", None),
            SlotSet("feedback_tipo", None),
            SlotSet("feedback_texto", None),
            SlotSet("motivo_soporte", None),         
            SlotSet("tipo_soporte", None),           
            SlotSet("soporte_mensaje", None),
            SlotSet("mensaje", None),
            SlotSet("ultimo_requerimiento", None),
            SlotSet("escalar_humano", False),
            SlotSet("derivacion_humano", False),
            SlotSet("soporte_form_fallback_count", 0),
            SlotSet("menu_actual", "principal"),    
            SlotSet("nombre", None),
            SlotSet("email", None),
            SlotSet("telefono", None),
            SlotSet("cedula", None),
            SlotSet("prefer_contacto", None),           
            SlotSet("auth_state", "inactive"),
            SlotSet("auth_token", None),
            SlotSet("user_token", None), 
            SlotSet("requires_auth", None),
            SlotSet("pending_action", None),
            SlotSet("auth_login_form", None),
            SlotSet("certificados", None),
            SlotSet("emocion_detectada", None),
            SlotSet("autosave_estado", None),
            SlotSet("reanudar_pendiente", False),
            SlotSet("evento_seguridad", None),
            SlotSet("user_id", None),
            SlotSet("session_id", None),
            SlotSet("password", None),
            SlotSet("slot_tipo_usuario", None),
            SlotSet("session_started_metadata", None),
            SlotSet("is_authenticated", False),
            SlotSet("esperando_pregunta_faq", False,),
            SlotSet("esperando_pqrsd", False,),
            SlotSet("menu_actual", None),

            ActiveLoop(None),
            SlotSet("requested_slot", None),
            

            FollowupAction("action_listen"),
        ]


# ================================================================
# 🧪 HEALTHCHECK
# ================================================================

class ActionPingServidor(Action):

    def name(self) -> str:
        return "action_ping_servidor"

    def run(
        self, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[str, Any]
    ) -> List[EventType]:

        logger.info(f"[ADMIN] ping user={tracker.sender_id}")

        dispatcher.utter_message(response="utter_ping_ok")
        return []


# ================================================================
# 👤 DEFAULT USER TYPE
# ================================================================

class ActionSetDefaultTipoUsuario(Action):

    def name(self) -> str:
        return "action_set_default_tipo_usuario"

    def run(
        self, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[str, Any]
    ) -> List[EventType]:

        logger.info(f"[ADMIN] set_default_user_type user={tracker.sender_id}")

        return [
            SlotSet(
                "slot_tipo_usuario",
                tracker.get_slot("slot_tipo_usuario") or "usuario"
            )
        ]


# ================================================================
# 🔐 TOKEN DISPLAY
# ================================================================

class ActionMostrarToken(Action):

    def name(self) -> str:
        return "action_mostrar_token"

    def run(
        self, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[str, Any]
    ) -> List[EventType]:

        tipo_usuario = tracker.get_slot("slot_tipo_usuario") or "usuario"
        user_token = tracker.get_slot("user_token") or "N/D"

        logger.info(
            f"[ADMIN] show_token user={tracker.sender_id} type={tipo_usuario}"
        )

        dispatcher.utter_message(
            response="utter_token_admin"
            if tipo_usuario == "admin"
            else "utter_token_actual",
            user_token=user_token,
        )

        return []


# ================================================================
# ⏱ RESET TURNOS CONVERSACIÓN
# ================================================================

class ActionResetTurnosConversacion(Action):

    def name(self) -> str:
        return "action_reset_turnos_conversacion"

    def run(
        self, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[str, Any]
    ) -> List[EventType]:

        logger.info(f"[ADMIN] reset_turnos user={tracker.sender_id}")

        return [
            SlotSet("turnos_conversacion", 0),
            SlotSet("sesion_larga", False),
        ]