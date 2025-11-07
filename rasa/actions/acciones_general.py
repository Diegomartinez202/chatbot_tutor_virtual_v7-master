# rasa/actions/acciones_general.py
from __future__ import annotations
from typing import List, Dict, Any
import json
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

from .common import jlog, logger, ACTIONS_PING_HELPDESK, HELPDESK_WEBHOOK, send_email, RESET_URL_BASE

class ActionEnviarCorreo(Action):
    def name(self) -> str:
        return "action_enviar_correo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List:
        email = (tracker.get_slot("email") or "").strip()
        if not email:
            dispatcher.utter_message(text="⚠️ No detecté tu correo. Por favor, escríbelo (ej: usuario@ejemplo.com).")
            return []
        reset_link = f"{RESET_URL_BASE}/reset?email={email}"
        body = ("Hola,\n\nHas solicitado recuperar tu contraseña.\n"
                f"Usa el siguiente enlace para continuar: {reset_link}\n\n"
                "Si no fuiste tú, ignora este mensaje.")
        sent = send_email("Recuperación de contraseña", body, email)
        jlog(logging.INFO, "action_enviar_correo", email=email, sent=bool(sent))
        dispatcher.utter_message(text="📬 Te envié un enlace de recuperación a tu correo." if sent
                                      else "ℹ️ Tu solicitud fue registrada. Revisa tu correo más tarde.")
        return []

class ActionConectarHumano(Action):
    def name(self) -> str:
        return "action_conectar_humano"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List:
        dispatcher.utter_message(text="🧑‍💻 ¡Listo! Te conecto con un agente humano, por favor espera…")
        return []

class ActionHealthCheck(Action):
    def name(self) -> str:
        return "action_health_check"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List:
        status: Dict[str, Any] = {"actions": "ok"}
        if ACTIONS_PING_HELPDESK:
            try:
                import requests
                r = requests.options(HELPDESK_WEBHOOK, timeout=3)
                status["helpdesk"] = f"ok ({r.status_code})"
            except Exception as e:
                status["helpdesk"] = f"error: {e}"
        else:
            status["helpdesk"] = "skip"
        dispatcher.utter_message(text=f"health: {json.dumps(status, ensure_ascii=False)}")
        return []

class ActionOfrecerContinuarTema(Action):
    def name(self) -> str:
        return "action_ofrecer_continuar_tema"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        dispatcher.utter_message(response="utter_ofrecer_continuar")
        return []
