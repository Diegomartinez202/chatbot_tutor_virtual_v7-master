# ruta: rasa/actions/acciones_autenticacion.py
from __future__ import annotations
import re
from typing import Dict, List, Any, Text, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType, FollowupAction
from rasa_sdk.types import DomainDict

# ====== Fallbacks seguros si no existe .common ======
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _has_auth(tracker: Tracker) -> bool:
    """Determina si el usuario está autenticado a partir del slot is_authenticated."""
    return bool(tracker.get_slot("is_authenticated"))

# ====== VALIDACIONES (si usas forms con validadores personalizados, opcional) ======
class ValidatePasswordRecoveryForm(Action):
    """Validador simple para password_recovery_form (Rasa 3 permite FormValidationAction,
    pero para reducir dependencias usamos Action normal con prompts claros)."""
    def name(self) -> Text: return "validate_password_recovery_form"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        # Este validador es opcional; puedes omitirlo si no lo llamas en rules.
        return []

# ====== ACCIONES DE AUTENTICACIÓN ======
class ActionCheckAuth(Action):
    def name(self) -> Text: return "action_check_auth"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        intent = ((tracker.latest_message or {}).get("intent") or {}).get("name") or ""
        authed = _has_auth(tracker)

        if intent in ("estado_estudiante", "ver_certificados"):
            if not authed:
                dispatcher.utter_message(response="utter_need_auth")
                return []
            # Delega al flujo correcto según intent
            next_action = "action_estado_estudiante" if intent == "estado_estudiante" else "action_ver_certificados"
            return [FollowupAction(next_action)]
        return []

class ActionIngresoZajuna(Action):
    def name(self) -> Text: return "action_ingreso_zajuna"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        dispatcher.utter_message(text="Abriendo flujo de inicio de sesión… Ingresa tu correo y contraseña.")
        return []

class ActionSetAuthenticatedTrue(Action):
    def name(self) -> Text: return "action_set_authenticated_true"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        return [SlotSet("is_authenticated", True)]

class ActionRecuperarContrasena(Action):
    def name(self) -> Text: return "action_recuperar_contrasena"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        email = (tracker.get_slot("email") or "").strip()
        if not EMAIL_RE.match(email):
            dispatcher.utter_message(text="📧 Necesito un correo válido para enviar el enlace de recuperación.")
            return []
        dispatcher.utter_message(text=f"Generando enlace de recuperación para {email}…")
        return []

class ActionEnviarCorreoRecuperacion(Action):
    def name(self) -> Text: return "action_enviar_correo_recuperacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        email = (tracker.get_slot("email") or "").strip()
        if EMAIL_RE.match(email):
            dispatcher.utter_message(text=f"📬 Se envió el correo de recuperación a {email}.")
        else:
            dispatcher.utter_message(text="No pude enviar el correo porque el email no es válido.")
        return []

class ActionSetAuthenticatedTrue(Action):
    def name(self) -> str:
        return "action_set_authenticated_true"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("is_authenticated", True)]
