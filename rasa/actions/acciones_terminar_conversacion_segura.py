# ruta: rasa/actions/acciones_terminar_conversacion_segura.py
from __future__ import annotations

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ConversationPaused, ConversationResumed
from rasa_sdk.types import DomainDict
from .acciones_llm import ActionResumenSesionLLM
from .acciones_llm import llm_summarize_with_ollama
import json


class ActionVerificarProcesoActivo(Action):
    def name(self) -> str:
        return "action_verificar_proceso_activo"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        proceso_activo = tracker.get_slot("proceso_activo")

        if proceso_activo:
            dispatcher.utter_message(
                text="Tienes un proceso activo. ¿Seguro que quieres terminar la conversación?"
            )
        else:
            dispatcher.utter_message(
                text="No hay procesos activos, puedo cerrar la conversación con seguridad."
            )

        return []


class ActionConfirmarCierreSeguroFinal(Action):
    """Evita colisión de nombre con otras definiciones de ActionConfirmarCierre."""

    def name(self) -> Text:
        return "action_confirmar_cierre_seguro_final"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # 1) Si la sesión fue larga, mostramos un resumen de la sesión (no se elimina nada previo)
        sesion_larga = bool(tracker.get_slot("sesion_larga"))
        if sesion_larga:
            try:
                ActionResumenSesionLLM().run(dispatcher, tracker, domain)
            except Exception:
                # No rompemos el flujo si falla el resumen
                pass

        # 2) Mantener tu lógica actual de mensaje de cierre seguro con LLM
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

            ultimo_intent = (tracker.latest_message.get("intent") or {}).get(
                "name", "desconocido"
            )

            texto_base = (
                "Cierre seguro de conversación con autosave o verificación previa.\n\n"
                "Contexto técnico (para que tú lo uses, no lo muestres tal cual):\n"
                f"- Último intent: {ultimo_intent}\n"
                f"- Slots relevantes (no sensibles): {json.dumps(safe_slots, ensure_ascii=False)[:800]}\n\n"
                "Genera un mensaje de despedida profesional que:\n"
                "- Indique que la conversación se cerró de forma segura.\n"
                "- Mencione de forma general que el progreso o la información clave ya quedó registrada.\n"
                "- Invite a volver cuando el estudiante lo necesite.\n"
                "- No invente certificados, notas ni estados académicos específicos.\n"
            )

            contexto_llm = {
                "flujo": "cierre_seguro",
                "tipo_cierre": "seguro_simple",
                "ultimo_intent": ultimo_intent,
            }

            mensaje_llm = llm_summarize_with_ollama(texto_base, contexto_llm)
            if mensaje_llm and mensaje_llm.strip():
                dispatcher.utter_message(text=mensaje_llm.strip())
        except Exception:
           
            pass

        # 3) Tu utter final sigue igual
        dispatcher.utter_message(response="utter_despedida_final")

        return [
            SlotSet("session_activa", False),
            SlotSet("confirmacion_cierre", None),
            SlotSet("proceso_activo", None),
            ConversationPaused(),
        ]

class ActionCancelarCierreSeguro(Action):
    def name(self) -> Text:
        return "action_cancelar_cierre_seguro"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_cancelar_cierre")
        return [SlotSet("confirmacion_cierre", None), ConversationResumed()]
