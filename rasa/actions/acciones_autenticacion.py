# rasa/actions/acciones_autenticacion.py
from __future__ import annotations
from typing import Dict, List, Any, Text
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType, FollowupAction
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict

from .common import _has_auth

class ValidateRecoveryForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_recovery_form"

    def validate_email(self, value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        v = (value or "").strip()
        from .common import EMAIL_RE
        if not EMAIL_RE.match(v):
            dispatcher.utter_message(text="📧 Ese email no parece válido. Escribe algo como usuario@dominio.com")
            return {"email": None}
        return {"email": v}

class ActionCheckAuth(Action):
    def name(self) -> Text:
        return "action_check_auth"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        intent = ((tracker.latest_message or {}).get("intent") or {}).get("name") or ""
        authed = _has_auth(tracker)
        if intent in ("estado_estudiante", "ver_certificados"):
            if not authed:
                dispatcher.utter_message(response="utter_need_auth")
                return []
            if intent == "estado_estudiante":
                return [FollowupAction("action_estado_estudiante")]
            elif intent == "ver_certificados":
                return [FollowupAction("action_ver_certificados")]
        return []

class ActionSyncAuthFromMetadata(Action):
    def name(self) -> Text:
        return "action_sync_auth_from_metadata"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        has_token = False
        try:
            md = tracker.latest_message.get("metadata") or {}
            auth = md.get("auth") or {}
            if isinstance(auth, dict):
                if auth.get("hasToken") is True:
                    has_token = True
                elif auth.get("token"):
                    has_token = True
        except Exception:
            has_token = False
        return [SlotSet("has_token", has_token)]

class ActionCheckAuthEstado(Action):
    def name(self) -> Text:
        return "action_check_auth_estado"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        meta = (tracker.latest_message or {}).get("metadata") or {}
        has_token = bool(((meta.get("auth") or {}).get("hasToken")))
        return [FollowupAction("action_estado_estudiante" if has_token else "utter_need_auth")]

class ActionSubmitRecovery(Action):
    def name(self) -> Text:
        return "action_submit_recovery"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        email = tracker.get_slot("email")
        if not email:
            dispatcher.utter_message(text="Indícame tu correo para enviarte la recuperación.")
            return []
        dispatcher.utter_message(text=f"Se envió un enlace de recuperación a {email}.")
        return []

class ActionSetAuthenticatedTrue(Action):
    def name(self) -> Text:
        return "action_set_authenticated_true"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [SlotSet("is_authenticated", True)]

class ActionMarkAuthenticated(Action):
    def name(self):
        return "action_mark_authenticated"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("is_authenticated", True)]

class ActionNecesitaAuth(Action):
    def name(self) -> str:
        return "action_necesita_auth"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        dispatcher.utter_message(text="Para continuar con esta acción necesitas iniciar sesión. ¿Deseas hacerlo ahora?")
        return []
