# ruta: rasa/actions/acciones_guardian.py
from __future__ import annotations
from typing import Any, Dict, List, Text
import logging

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType, FollowupAction

from utils.guardian_client import GuardianClient
from .acciones_llm import llm_summarize_with_ollama

logger = logging.getLogger(__name__)

MAX_INTENTOS_FORM = 3  # puedes moverlo a ENV si lo deseas


# ======================================================
# 🛡️ AUTOSAVE / SNAPSHOT para Guardian
# ======================================================
class ActionAutosaveSnapshot(Action):
    def name(self) -> Text:
        return "action_autosave_snapshot"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        gc = GuardianClient(
            base_url="http://autosave-guardian:8080",
            username="admin",
            password="admin123",
            timeout=4.0,
            max_retries=2,
        )

        data = {
            "latest_intent": tracker.latest_message.get("intent", {}).get("name"),
            "slots": tracker.current_slot_values(),
            "events_count": len(tracker.events) if tracker.events else 0,
        }

        ok = gc.autosave_create(sender_id=tracker.sender_id, data=data)

        if ok:
            # 🧾 Texto base técnico para el usuario
            texto_base = (
                "Se guardó un snapshot automático de la sesión para poder retomarla más adelante "
                "o para que un asesor humano tenga contexto del caso. "
                "Aclara que no se guarda la contraseña ni datos bancarios, solo el progreso de la conversación "
                "y algunos datos técnicos necesarios."
            )
            contexto_llm = {
                "flujo": "guardian_autosave",
                "events_count": data["events_count"],
            }

            try:
                mensaje = llm_summarize_with_ollama(texto_base, contexto_llm)
                dispatcher.utter_message(text=mensaje)
            except Exception:
                # Fallback seguro si el LLM falla
                logger.exception("Error generando mensaje LLM en ActionAutosaveSnapshot")
                dispatcher.utter_message(text="✅ Snapshot guardado correctamente.")
        else:
            dispatcher.utter_message(
                text="⚠️ No fue posible guardar el snapshot en este momento."
            )

        gc.log_event(
            "action_autosave_snapshot_called",
            {"sender_id": tracker.sender_id},
        )

        return []
