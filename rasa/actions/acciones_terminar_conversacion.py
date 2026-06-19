# ruta: rasa/actions/acciones_terminar_conversacion.py
from __future__ import annotations

import json
import logging
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import (
    SlotSet, 
    ConversationPaused, 
    ConversationResumed,
    EventType
)
from .core.llm_engine import run_llm

logger = logging.getLogger(__name__)


class ActionConfirmarCierre(Action):
    def name(self) -> Text:
        return "action_confirmar_cierre"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Tipado oficial con DomainDict
    ) -> List[EventType]:  # MEJORA: Firma tipada correctamente a List[EventType]
        dispatcher.utter_message(response="utter_confirmar_cierre")
        return [SlotSet("confirmacion_cierre", "pendiente")]


class ActionFinalizarConversacion(Action):

    def name(self) -> Text:
        return "action_finalizar_conversacion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Tipado oficial con DomainDict
    ) -> List[EventType]:  # MEJORA: Firma tipada correctamente a List[EventType]

        latest = tracker.latest_message or {}

        ultimo_intent = (
            (latest.get("intent") or {}).get(
                "name",
                "desconocido",
            )
        )

        logger.info(
            "[FIN_CONVERSACION] user=%s intent=%s",
            tracker.sender_id,
            ultimo_intent,
        )

        # =====================================================
        # RESUMEN DE SESIÓN (OPCIONAL)
        # =====================================================
        sesion_larga = bool(tracker.get_slot("sesion_larga"))

        if sesion_larga:
            try:
                resumen_sesion = run_llm(
                    prompt=(
                        "Genera un resumen muy breve de la atención "
                        "brindada durante esta sesión para despedir "
                        "al usuario."
                    ),
                    tracker=tracker,
                    context={
                        "flujo": "resumen_sesion",
                        "ultimo_intent": ultimo_intent,
                    },
                    fallback=(
                        "✅ La sesión fue atendida correctamente. "
                        "Gracias por utilizar el asistente."
                    ),
                )

                if (
                    resumen_sesion
                    and isinstance(resumen_sesion, str)
                    and resumen_sesion.strip()
                ):
                    dispatcher.utter_message(text=resumen_sesion.strip())

            except Exception:
                logger.exception("[CIERRE] error generando resumen")

        # =====================================================
        # MENSAJE FINAL DE DESPEDIDA
        # =====================================================
        try:
            slots = tracker.current_slot_values() or {}

            # Filtro estricto de privacidad de datos (Sanitización del contexto)
            SENSITIVE_SLOTS = {
                "user_token",
                "auth_token",
                "password",
                "email",
                "correo",
                "nombre",
            }

            safe_slots = {
                k: v
                for k, v in slots.items()
                if k not in SENSITIVE_SLOTS
                and v not in (
                    None,
                    "",
                    {},
                )
            }

            texto_base = (
                "Genera un mensaje final de despedida "
                "amable, profesional y breve para un estudiante."
            )

            contexto_llm = {
                "flujo": "cierre_conversacion",
                "ultimo_intent": ultimo_intent,
                "slots_relevantes": json.dumps(
                    safe_slots,
                    ensure_ascii=False,
                )[:1000],
            }

            resumen_llm = run_llm(
                prompt=texto_base,
                tracker=tracker,
                context=contexto_llm,
                fallback=(
                    "Gracias por utilizar el asistente virtual. "
                    "Estaremos disponibles cuando necesites ayuda nuevamente."
                ),
            )

            if (
                resumen_llm
                and isinstance(resumen_llm, str)
                and resumen_llm.strip()
            ):
                dispatcher.utter_message(text=resumen_llm.strip())
            else:
                dispatcher.utter_message(response="utter_despedida_profesional")

        except Exception:
            logger.exception("[FIN_CONVERSACION] llm cierre error")
            dispatcher.utter_message(response="utter_despedida_profesional")

        return [
            SlotSet("session_activa", False),
            SlotSet("confirmacion_cierre", None),
            SlotSet("encuesta_activa", None),
            SlotSet("escalar_humano", False),
            ConversationPaused(),  # Congela el tracker de Rasa ante nuevas entradas del canal
        ]


class ActionCancelarCierre(Action):
    def name(self) -> Text:
        return "action_cancelar_cierre"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Tipado oficial con DomainDict
    ) -> List[EventType]:  # MEJORA: Firma tipada correctamente a List[EventType]

        dispatcher.utter_message(response="utter_confirmar_cierre")
        dispatcher.utter_message(response="utter_cierre_cancelado")
        dispatcher.utter_message(response="utter_volver_menu")

        return [
            SlotSet("confirmacion_cierre", None),
            ConversationResumed(),  # Asegura la reactivación del procesamiento de políticas en Rasa Core
        ]