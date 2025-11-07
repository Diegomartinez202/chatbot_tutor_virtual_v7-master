# rasa/actions/acciones_soporte.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Text
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict

from .common import (
    logger, jlog, EMAIL_RE, HELPDESK_WEBHOOK, HELPDESK_TOKEN,
    _entity_value, _json_payload_from_text, post_json_with_retries
)

class ValidateSoporteForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_soporte_form"

    def validate_nombre(self, value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        v = (value or "").strip()
        if len(v) < 3:
            dispatcher.utter_message(text="⚠️ El nombre debe tener al menos 3 caracteres.")
            return {"nombre": None}
        if len(v) > 120:
            dispatcher.utter_message(text="⚠️ El nombre es muy largo. ¿Puedes abreviarlo un poco?")
            return {"nombre": None}
        return {"nombre": v}

    def validate_email(self, value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        v = (value or "").strip()
        if not EMAIL_RE.match(v):
            dispatcher.utter_message(text="📧 Ese email no parece válido. Escribe algo como usuario@dominio.com")
            return {"email": None}
        return {"email": v}

    def validate_mensaje(self, value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        v = (value or "").strip()
        if len(v) < 8:
            dispatcher.utter_message(text="📝 Dame un poco más de detalle del problema (mínimo 8 caracteres).")
            return {"mensaje": None}
        if len(v) > 5000:
            dispatcher.utter_message(text="📝 El mensaje es muy largo. Intenta resumirlo (máx. 5000).")
            return {"mensaje": None}
        return {"mensaje": v}

class ActionEnviarSoporte(Action):
    def name(self) -> Text:
        return "action_enviar_soporte"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        nombre_ent = _entity_value(tracker, "nombre")
        email_ent = _entity_value(tracker, "email")
        mensaje_ent = _entity_value(tracker, "mensaje")

        last_text = (tracker.latest_message.get("text") or "").strip()
        json_payload = _json_payload_from_text(last_text)

        nombre_slot = (tracker.get_slot("nombre") or "").strip()
        email_slot = (tracker.get_slot("email") or "").strip()
        mensaje_slot = (tracker.get_slot("mensaje") or "").strip()

        nombre = (nombre_ent or json_payload.get("nombre") or nombre_slot or "Usuario").strip()
        email = (email_ent or json_payload.get("email") or email_slot or "sin-correo@zajuna.edu").strip()
        mensaje = (mensaje_ent or json_payload.get("mensaje") or mensaje_slot or "").strip()
        if not mensaje:
            mensaje = last_text if not last_text.startswith("/enviar_soporte") else "Solicitud de soporte (sin detalle)."

        if len(nombre) > 120:
            nombre = nombre[:120].rstrip() + "…"
        if len(mensaje) > 5000:
            mensaje = mensaje[:5000].rstrip() + "…"
        if not EMAIL_RE.match(email):
            logger.warning("[actions] Email inválido en action_enviar_soporte: %r, usando fallback.", email)
            email = "sin-correo@zajuna.edu"

        meta: Dict[str, Any] = {
            "rasa_sender_id": tracker.sender_id,
            "latest_intent": (tracker.latest_message.get("intent") or {}).get("name"),
            "timestamp": int(time.time()),
            "slots": tracker.current_slot_values(),
            "metadata": (tracker.latest_message or {}).get("metadata") or {},
        }

        payload = {
            "name": nombre, "email": email,
            "subject": "Soporte rápido (Rasa)", "message": mensaje or "Solicitud de soporte (sin detalle).",
            "conversation_id": tracker.sender_id, "metadata": meta,
        }

        headers = {"Content-Type": "application/json"}
        if HELPDESK_TOKEN:
            headers["Authorization"] = f"Bearer {HELPDESK_TOKEN}"

        resp = post_json_with_retries(HELPDESK_WEBHOOK, payload, headers)
        ok = bool(resp and 200 <= resp.status_code < 300)
        jlog(logging.INFO, "action_enviar_soporte", ok=ok, status_code=getattr(resp, "status_code", None))
        if ok:
            dispatcher.utter_message(text="✅ He enviado tu solicitud de soporte. Un agente te contactará.")
            return []
        else:
            code = getattr(resp, "status_code", "sin-respuesta")
            logger.error("[actions] action_enviar_soporte: fallo %s | %s", code, getattr(resp, "text", ""))
            dispatcher.utter_message(text="⚠️ No pude registrar el soporte ahora mismo. Intentaremos de nuevo.")
            return []

class ActionSoporteSubmit(Action):
    def name(self) -> Text:
        return "action_soporte_submit"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        nombre = (tracker.get_slot("nombre") or "").strip()
        email = (tracker.get_slot("email") or "").strip()
        mensaje = (tracker.get_slot("mensaje") or "").strip()

        if not (nombre and email and mensaje):
            dispatcher.utter_message(text="❌ Faltan datos para crear el ticket de soporte.")
            return []

        meta: Dict[str, Any] = {
            "rasa_sender_id": tracker.sender_id,
            "latest_intent": (tracker.latest_message.get("intent") or {}).get("name"),
            "timestamp": int(time.time()),
            "slots": tracker.current_slot_values(),
            "metadata": (tracker.latest_message or {}).get("metadata") or {},
        }

        payload = {
            "name": nombre, "email": email, "subject": "Soporte técnico (Rasa)",
            "message": mensaje, "conversation_id": tracker.sender_id, "metadata": meta,
        }

        headers = {"Content-Type": "application/json"}
        if HELPDESK_TOKEN:
            headers["Authorization"] = f"Bearer {HELPDESK_TOKEN}"

        resp = post_json_with_retries(HELPDESK_WEBHOOK, payload, headers)
        ok = bool(resp and 200 <= resp.status_code < 300)
        jlog(logging.INFO, "action_soporte_submit", ok=ok, status_code=getattr(resp, "status_code", None))
        if ok:
            tid = None
            try:
                data = resp.json(); tid = (data or {}).get("ticket_id") or (data or {}).get("id")
            except Exception:
                pass
            if tid:
                dispatcher.utter_message(text=f"🎫 Ticket creado correctamente. ID: {tid}")
            else:
                dispatcher.utter_message(response="utter_soporte_creado")
            return [SlotSet("nombre", None), SlotSet("email", None), SlotSet("mensaje", None)]
        else:
            code = getattr(resp, "status_code", "sin-respuesta")
            logger.error("[actions] Helpdesk respondió %s: %s", code, getattr(resp, "text", ""))
            dispatcher.utter_message(response="utter_soporte_error")
            return []

class ActionSubmitSoporte(Action):
    def name(self) -> Text:
        return "action_submit_soporte"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        return ActionSoporteSubmit().run(dispatcher, tracker, domain)

class ActionDerivarYRegistrarHumano(Action):
    def name(self) -> Text:
        return "action_derivar_y_registrar_humano"

    def run(self, dispatcher, tracker, domain):
        # Espacio para registrar en Helpdesk/Mongo si deseas
        dispatcher.utter_message(text="Te conecto con un agente humano en breve.")
        return []
