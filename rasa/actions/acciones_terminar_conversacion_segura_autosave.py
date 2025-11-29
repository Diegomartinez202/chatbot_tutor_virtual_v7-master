# ruta: rasa/actions/acciones_terminar_conversacion_segura_autosave.py
from __future__ import annotations

from typing import Any, Text, Dict, List
from datetime import datetime
import json

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ConversationPaused, ConversationResumed
from .acciones_llm import ActionResumenSesionLLM
from .acciones_llm import llm_summarize_with_ollama


class ActionVerificarProcesoActivoAutosave(Action):
    def name(self) -> Text:
        return "action_verificar_proceso_activo_autosave"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
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
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
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
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        encuesta_incompleta = bool(tracker.get_slot("encuesta_incompleta"))
        sesion_larga = bool(tracker.get_slot("sesion_larga"))

        # ================================
        # 1) Mensaje de cierre autosave con LLM (TU LÓGICA ORIGINAL)
        # ================================
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
                if k not in SENSITIVE_SLOTS and v not in (None, "", {})
            }

            tipo_cierre = "autosave_guardado" if encuesta_incompleta else "autosave_descartado"
            ultimo_intent = (tracker.latest_message.get("intent") or {}).get(
                "name", "desconocido"
            )

            texto_base = (
                "Cierre de conversación con lógica de autosave para encuestas.\n\n"
                f"- ¿Había encuesta incompleta?: {encuesta_incompleta}\n"
                f"- Último intent: {ultimo_intent}\n"
                f"- Slots relevantes (no sensibles): {json.dumps(safe_slots, ensure_ascii=False)[:800]}\n\n"
                "Genera un mensaje corto y empático que:\n"
                "- Si la encuesta estaba incompleta, indique que el progreso quedó guardado y podrá retomarse.\n"
                "- Si no había encuesta pendiente, indique que se cerró la conversación sin guardar nada adicional.\n"
                "- Agradezca al usuario su tiempo.\n"
                "- Invite a volver cuando lo necesite.\n"
                "- No mencione datos concretos ni sensibles.\n"
            )

            contexto_llm = {
                "flujo": "cierre_autosave",
                "tipo_cierre": tipo_cierre,
                "encuesta_incompleta": encuesta_incompleta,
            }

            mensaje_llm = llm_summarize_with_ollama(texto_base, contexto_llm)
            if mensaje_llm and mensaje_llm.strip():
                dispatcher.utter_message(text=mensaje_llm.strip())
        except Exception:
            # Si falla el LLM, seguimos con el resto del flujo
            pass

        # ================================
        # 2) Resumen de sesión SOLO si la sesión fue larga
        # ================================
        if sesion_larga:
            try:
                ActionResumenSesionLLM().run(dispatcher, tracker, domain)
            except Exception:
                # No bloquea el cierre si el resumen falla
                pass

        # ================================
        # 3) Mantener tu comportamiento original de cierre
        # ================================
        if encuesta_incompleta:
            dispatcher.utter_message(response="utter_despedida_final")
            return [
                SlotSet("session_activa", False),
                SlotSet("confirmacion_cierre", None),
                SlotSet("encuesta_incompleta", False),
                ConversationPaused(),
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
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_cancelar_cierre")
        return [SlotSet("confirmacion_cierre", None), ConversationResumed()]
