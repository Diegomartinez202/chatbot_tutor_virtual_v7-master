# ruta: rasa/actions/acciones_terminar_conversacion_segura_autosave.py
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import (
    SlotSet, 
    ConversationPaused, 
    ConversationResumed,
    EventType  # MEJORA: Tipado oficial para eventos mutadores de Rasa
)
from .core.llm_engine import run_llm

logger = logging.getLogger(__name__)


class ActionVerificarProcesoActivoAutosave(Action):
    def name(self) -> Text:
        return "action_verificar_proceso_activo_autosave"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Uso de DomainDict
    ) -> List[EventType]:  # MEJORA: Retorno estricto List[EventType]
        proceso_activo = tracker.get_slot("proceso_activo")
        encuesta_incompleta = tracker.get_slot("encuesta_incompleta")

        if encuesta_incompleta:
            dispatcher.utter_message(response="utter_confirmar_cierre_con_autosave")
        elif proceso_activo:
            dispatcher.utter_message(response="utter_confirmar_cierre_seguro")
        else:
            dispatcher.utter_message(response="utter_confirmar_cierre")

        return [SlotSet("confirmacion_cierre", "pendiente")]


class ActionGuardarEncuestaIncompleta(Action):
    def name(self) -> Text:
        return "action_guardar_encuesta_incompleta"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Uso de DomainDict
    ) -> List[EventType]:  # MEJORA: Retorno estricto List[EventType]
        usuario = tracker.sender_id
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        dispatcher.utter_message(
            text=f"Guardando tu progreso de encuesta ({fecha}) para el usuario {usuario}…"
        )
        dispatcher.utter_message(
            text="✅ Encuesta parcial registrada correctamente."
        )
        return [
            SlotSet("encuesta_incompleta", False),
            SlotSet("proceso_activo", None),
        ]


class ActionConfirmarCierreAutosave(Action):
    def name(self) -> Text:
        return "action_confirmar_cierre_autosave"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Uso de DomainDict
    ) -> List[EventType]:  # MEJORA: Retorno estricto List[EventType]

        encuesta_incompleta = bool(tracker.get_slot("encuesta_incompleta"))
        sesion_larga = bool(tracker.get_slot("sesion_larga"))
        
        # MEJORA: Extracción unificada del intent para evitar re-cálculos en bloques independientes
        latest = tracker.latest_message or {}
        ultimo_intent = (latest.get("intent") or {}).get("name") or "desconocido"

        # =====================================================
        # MENSAJE DE CIERRE VÍA LLM
        # =====================================================
        try:
            slots = tracker.current_slot_values() or {}

            # Filtro riguroso para evitar la fuga de PII hacia servicios de lenguaje externos
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

            tipo_cierre = (
                "autosave_guardado"
                if encuesta_incompleta
                else "autosave_descartado"
            )

            texto_base = (
                "Genera un mensaje breve de cierre para un estudiante. "
                "Si existía una encuesta incompleta indica que el progreso "
                "quedó guardado. Si no existía, indica que la conversación "
                "se cerró normalmente."
            )

            contexto_llm = {
                "flujo": "cierre_autosave",
                "tipo_cierre": tipo_cierre,
                "encuesta_incompleta": encuesta_incompleta,
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
                    "👋 Gracias por utilizar el asistente. "
                    "Tu sesión ha sido cerrada correctamente."
                ),
            )

            if (
                mensaje_llm
                and isinstance(mensaje_llm, str)
                and mensaje_llm.strip()
            ):
                dispatcher.utter_message(text=mensaje_llm.strip())

        except Exception:
            logger.exception("[CIERRE_AUTOSAVE] error generando mensaje LLM")

        # =====================================================
        # RESUMEN DE SESIÓN (SI APLICA)
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
                logger.exception("[CIERRE_AUTOSAVE] error generando resumen")

        # =====================================================
        # RETORNO DE EVENTOS SEGÚN ESTADO DE LA ENCUESTA
        # =====================================================
        if encuesta_incompleta:
            dispatcher.utter_message(response="utter_despedida")
            return [
                SlotSet("session_activa", False),
                SlotSet("confirmacion_cierre", None),
                SlotSet("encuesta_incompleta", False),
                ConversationPaused(),  # Asegura el congelamiento del canal
            ]

        dispatcher.utter_message(response="utter_despedida_sin_guardar")
        return [
            SlotSet("session_activa", False),
            SlotSet("confirmacion_cierre", None),
            ConversationPaused(),
        ]


class ActionCancelarCierreAutosave(Action):
    def name(self) -> Text:
        return "action_cancelar_cierre_autosave"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Uso de DomainDict
    ) -> List[EventType]:  # MEJORA: Retorno estricto List[EventType]

        dispatcher.utter_message(response="utter_cancelar_cierre")
        return [
            SlotSet("confirmacion_cierre", None), 
            ConversationResumed()  # Reactiva las predicciones del Core
        ]