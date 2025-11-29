# ruta: rasa/actions/acciones_terminar_conversacion.py
from __future__ import annotations

from typing import Any, Text, Dict, List
import json

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ConversationPaused, ConversationResumed
from .acciones_llm import ActionResumenSesionLLM
from .acciones_llm import llm_summarize_with_ollama


class ActionConfirmarCierre(Action):
    def name(self) -> Text:
        return "action_confirmar_cierre"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_confirmar_cierre")
        return [SlotSet("confirmacion_cierre", "pendiente")]


class ActionFinalizarConversacion(Action):
    def name(self) -> Text:
        return "action_finalizar_conversacion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        print(
            f"[FIN CONVERSACIÓN] user_id={tracker.sender_id} "
            f"last_intent={tracker.latest_message.get('intent', {}).get('name')}"
        )

        # 💡 Si la sesión fue "larga", generamos un resumen antes de despedir
        sesion_larga = bool(tracker.get_slot("sesion_larga"))
        if sesion_larga:
            try:
                ActionResumenSesionLLM().run(dispatcher, tracker, domain)
            except Exception:
                # No rompemos el cierre si el resumen falla
                pass

        # Mensaje de despedida profesional (ya lo tenías)
        dispatcher.utter_message(response="utter_despedida_profesional")

        return [
            SlotSet("session_activa", False),
            SlotSet("confirmacion_cierre", None),
            SlotSet("encuesta_activa", None),
            SlotSet("escalar_humano", False),
            ConversationPaused(),
        ]


        # ================================
        # ✨ Resumen de sesión con LLM
        # ================================
        try:
            slots = tracker.current_slot_values() or {}

            # Evitar datos sensibles
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
                "Genera un mensaje de cierre amable y profesional para un estudiante del SENA.\n\n"
                "Contexto técnico de la sesión (solo para que tú lo interpretes, NO lo muestres como JSON literal):\n"
                f"- Último intent detectado: {ultimo_intent}\n"
                f"- Slots relevantes (no sensibles): {json.dumps(safe_slots, ensure_ascii=False)[:1000]}\n\n"
                "El mensaje debe:\n"
                "- Agradecer el tiempo del usuario.\n"
                "- Mencionar de forma general que se trabajó en temas académicos o de soporte.\n"
                "- Invitar a volver cuando lo necesite.\n"
                "- No inventar datos concretos de certificados, notas ni estados.\n"
            )

            contexto_llm = {
                "flujo": "cierre_conversacion",
                "tipo_cierre": "normal",
                "ultimo_intent": ultimo_intent,
            }

            resumen_llm = llm_summarize_with_ollama(texto_base, contexto_llm)
            if resumen_llm and resumen_llm.strip():
                dispatcher.utter_message(text=resumen_llm.strip())
        except Exception:
            # No rompemos el cierre si falla el LLM
            pass

        # Mensaje estándar que ya tenías
        dispatcher.utter_message(response="utter_despedida_profesional")

        return [
            SlotSet("session_activa", False),
            SlotSet("confirmacion_cierre", None),
            SlotSet("encuesta_activa", None),
            SlotSet("escalar_humano", False),
            ConversationPaused(),
        ]


class ActionCancelarCierre(Action):
    def name(self) -> Text:
        return "action_cancelar_cierre"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_cancelar_cierre")
        dispatcher.utter_message(response="utter_cierre_cancelado")
        # Asumo que tienes un utter_volver_menu; si no, puedes cambiarlo por utter_volver_menu_principal
        dispatcher.utter_message(response="utter_volver_menu")

        return [
            SlotSet("confirmacion_cierre", None),
            ConversationResumed(),
        ]
