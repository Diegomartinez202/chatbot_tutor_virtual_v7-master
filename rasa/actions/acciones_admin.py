# ruta: rasa/actions/acciones_admin.py
from __future__ import annotations

import logging
from typing import List, Any, Dict

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType
from rasa_sdk.events import FollowupAction
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

        dispatcher.utter_message(response="utter_reinicio_confirmado")

        return [
            Restarted(),
            SlotSet("session_activa", True),
            SlotSet("encuesta_activa", False),       
            SlotSet("encuesta_incompleta", False),  
            SlotSet("proceso_activo", None),
            SlotSet("tema_actual", None),
            SlotSet("tema_consulta", 0),
            SlotSet("nivel_explicacion", False),
            SlotSet("ultima_respuesta_llm", False),
            SlotSet("rol_academico", ""),
            SlotSet("materia_detectada"),
            SlotSet("confirmacion_cierre", None),
            SlotSet("turnos_conversacion", 0),
            SlotSet("sesion_larga", False),
            SlotSet("is_authenticated", False),
            SlotSet("user_token", ""),
            SlotSet("auth_state", "inactive"),
            FollowupAction("action_listen"),
            FollowupAction("esperando_tema"),
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