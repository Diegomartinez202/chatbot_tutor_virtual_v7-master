# rasa/actions/guardian_actions.py
from __future__ import annotations

from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from utils.guardian_client import GuardianClient


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

        # datos simples de ejemplo
        data = {
            "latest_intent": tracker.latest_message.get("intent", {}).get("name"),
            "slots": tracker.current_slot_values(),
            "events_count": len(tracker.events) if tracker.events else 0,
        }

        ok = gc.autosave_create(sender_id=tracker.sender_id, data=data)

        if ok:
            dispatcher.utter_message(text="✅ Snapshot guardado correctamente.")
        else:
            dispatcher.utter_message(text="⚠️ No fue posible guardar el snapshot.")

        # También podrías loggear un evento (no bloqueante para UX)
        gc.log_event("action_autosave_snapshot_called", {"sender_id": tracker.sender_id})

        return []
