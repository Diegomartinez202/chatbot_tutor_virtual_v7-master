# ruta: rasa/actions/acciones_terminar_conversacion_segura.py
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
    EventType,  # MEJORA: Importación para tipado de retornos explícitos
)

from .core.llm_engine import run_llm

logger = logging.getLogger(__name__)


class ActionVerificarProcesoActivo(Action):

    def name(self) -> str:
        return "action_verificar_proceso_activo"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:  # MEJORA: Estandarización del tipo de retorno a List[EventType]

        proceso_activo = tracker.get_slot("proceso_activo")

        if proceso_activo:
            dispatcher.utter_message(
                text=(
                    "Tienes un proceso activo. "
                    "¿Seguro que quieres terminar la conversación?"
                )
            )
        else:
            dispatcher.utter_message(
                text=(
                    "No hay procesos activos, "
                    "puedo cerrar la conversación con seguridad."
                )
            )

        return []


class ActionConfirmarCierreSeguroFinal(Action):

    def name(self) -> Text:
        return "action_confirmar_cierre_seguro_final"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Cambio de Dict[Text, Any] a DomainDict
    ) -> List[EventType]:  # MEJORA: Cambio de List[Dict[Text, Any]] a List[EventType]

        latest = tracker.latest_message or {}

        ultimo_intent = (
            (latest.get("intent") or {}).get(
                "name",
                "desconocido",
            )
        )

        sesion_larga = bool(tracker.get_slot("sesion_larga"))

        # =====================================================
        # RESUMEN DE SESIÓN
        # =====================================================
        if sesion_larga:
            try:
                resumen_sesion = run_llm(
                    prompt=(
                        "Genera un resumen muy breve de la atención "
                        "brindada durante esta sesión."
                    ),
                    tracker=tracker,
                    context={
                        "flujo": "resumen_sesion_segura",
                        "ultimo_intent": ultimo_intent,
                    },
                    fallback=(
                        "✅ La sesión fue atendida correctamente."
                    ),
                )

                if (
                    resumen_sesion
                    and isinstance(resumen_sesion, str)
                    and resumen_sesion.strip()
                ):
                    dispatcher.utter_message(text=resumen_sesion.strip())

            except Exception:
                logger.exception("[CIERRE_SEGURO] resumen error")

        # =====================================================
        # DESPEDIDA SEGURA (Sanitización e Inferencia del Contexto)
        # =====================================================
        try:
            slots = tracker.current_slot_values() or {}

            SENSITIVE_SLOTS = {
                "user_token",
                "auth_token",
                "password",
                "cedula",
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
                "Genera una despedida profesional para "
                "un cierre seguro de conversación."
            )

            contexto_llm = {
                "flujo": "cierre_seguro",
                "tipo_cierre": "seguro_simple",
                "ultimo_intent": ultimo_intent,
                "slots_relevantes": json.dumps(
                    safe_slots,
                    ensure_ascii=False,
                )[:800],
            }

            mensaje_llm = run_llm(
                prompt=texto_base,
                tracker=tracker,
                context=contexto_llm,
                fallback=(
                    "👋 La conversación se cerró correctamente. "
                    "Tu información relevante ha sido conservada "
                    "y podrás continuar cuando lo necesites."
                ),
            )

            if (
                mensaje_llm
                and isinstance(mensaje_llm, str)
                and mensaje_llm.strip()
            ):
                dispatcher.utter_message(text=mensaje_llm.strip())
            else:
                dispatcher.utter_message(response="utter_despedida_final")

        except Exception:
            logger.exception("[CIERRE_SEGURO] llm error")
            dispatcher.utter_message(response="utter_despedida_final")

        return [
            SlotSet("session_activa", False),
            SlotSet("confirmacion_cierre", None),
            SlotSet("proceso_activo", None),  # Liberación explícita del estado de bloqueo
            ConversationPaused(),
        ]


class ActionCancelarCierreSeguro(Action):

    def name(self) -> Text:
        return "action_cancelar_cierre_seguro"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Cambio de Dict[Text, Any] a DomainDict
    ) -> List[EventType]:  # MEJORA: Cambio de List[Dict[Text, Any]] a List[EventType]

        dispatcher.utter_message(response="utter_cancelar_cierre")

        return [
            SlotSet("confirmacion_cierre", None),
            ConversationResumed(),
        ]