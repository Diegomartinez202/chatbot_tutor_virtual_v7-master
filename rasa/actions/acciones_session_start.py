# ruta: rasa/actions/acciones_session_start.py
from __future__ import annotations

from typing import Any, Dict, List, Text, Optional
import logging
from rasa_sdk.events import FollowupAction
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import (
    SessionStarted,
    ActionExecuted,
    SlotSet,
    EventType,
)

logger = logging.getLogger(__name__)


class ActionSessionStart(Action):

    def name(self) -> Text:
        return "action_session_start"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Tipado oficial con DomainDict
    ) -> List[EventType]:

        # Inicialización oficial de la sesión en el Tracker Store
        events: List[EventType] = [SessionStarted()]

        # ==========================================================
        # RESET CONTROLADO DE SLOTS TEMPORALES
        # ==========================================================
        slots_to_reset = [
            "nombre",
            "email",
            "cedula",
            "motivo_soporte",
            "prefer_contacto",
            "telefono",
            "soporte_mensaje",
            "mensaje",
            "tipo_soporte",
            "escalar_humano",
        ]

        for slot_name in slots_to_reset:
            events.append(SlotSet(slot_name, None))

        # ==========================================================
        # METADATA SAFE
        # ==========================================================
        latest_message = tracker.latest_message or {}
        metadata = latest_message.get("metadata") or {}

        token: Optional[str] = None  # MEJORA: Tipado robusto explícito

        # ==========================================================
        # AUTH STRUCTURE
        # ==========================================================
        auth_meta = metadata.get("auth")

        if isinstance(auth_meta, dict):
            token = (
                auth_meta.get("token")
                or auth_meta.get("access_token")
                or auth_meta.get("id_token")
            )

            claims = auth_meta.get("claims")
            if isinstance(claims, dict):
                token = (
                    token
                    or claims.get("token")
                    or claims.get("access_token")
                    or claims.get("id_token")
                )

        # ==========================================================
        # FALLBACKS COMPATIBLES
        # ==========================================================
        token = (
            token
            or metadata.get("auth_token")
            or metadata.get("zajuna_token")
            or metadata.get("token")
        )

        # ==========================================================
        # AUTH STATE
        # ==========================================================
        if token:
            logger.info("[SESSION_START] Token detectado y parseado con éxito para user_id=%s", tracker.sender_id)
            events.extend(
                [
                    SlotSet("auth_token", token),
                    SlotSet("is_authenticated", True),
                ]
            )
        else:
            logger.info("[SESSION_START] Conexión anónima o sin token para user_id=%s", tracker.sender_id)
            events.extend(
                [
                    SlotSet("auth_token", None),
                    SlotSet("is_authenticated", False),
                ]
            )

        # ==========================================================
        # FLUJO INICIAL
        # ==========================================================
        # Disparamos la acción de saludo inicial de forma explícita
        events.append(
            FollowupAction("action_ir_menu_principal")
        )
        
        # NOTA DE REFACCIÓN: Se remueve el retorno manual de 'action_listen' para permitir 
        # que Rasa Core maneje de forma nativa la predicción del ciclo de escucha.

        return events