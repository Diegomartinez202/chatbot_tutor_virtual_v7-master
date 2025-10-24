# rasa/actions/actions.py
from __future__ import annotations

import os
import re
import time
import json
import smtplib
import logging
from typing import Any, Dict, List, Optional, Text

import requests
from email.mime.text import MIMEText

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.types import DomainDict
from rasa_sdk.forms import FormValidationAction  # Rasa SDK 3.x

__all__ = [
    "ValidateSoporteForm",
    "ValidateRecoveryForm",
    "ActionEnviarCorreo",
    "ActionEnviarSoporte",
    "ActionSoporteSubmit",
    "ActionConectarHumano",
    "ActionHealthCheck",
    "ActionCheckAuth",
]

# =========================
#    Logging estructurado
# =========================
LOG_LEVEL = (os.getenv("ACTIONS_LOG_LEVEL") or "INFO").upper()
LOG_FILE = (os.getenv("ACTIONS_LOG_FILE") or "").strip()

logger = logging.getLogger("rasa.actions")
if not logger.handlers:
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logger.level)
    stream_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(stream_handler)

    if LOG_FILE:
        try:
            file_handler = logging.FileHandler(LOG_FILE)
            file_handler.setLevel(logger.level)
            file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning("No se pudo abrir ACTIONS_LOG_FILE=%s: %s", LOG_FILE, e)

def jlog(level: int, event: str, **fields: Any) -> None:
    """Loggea un objeto JSON en una sola línea."""
    try:
        payload = {"event": event, **fields}
        logger.log(level, json.dumps(payload, ensure_ascii=False))
    except Exception as e:
        logger.log(level, f"{event} (json-fail): {fields} err={e}")

# =========================
#    Config & Constantes
# =========================
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

HELPDESK_WEBHOOK: str = (os.getenv("HELPDESK_WEBHOOK") or "http://localhost:8000/api/helpdesk/tickets").strip()
HELPDESK_TOKEN: str = (os.getenv("HELPDESK_TOKEN") or "").strip()

# SMTP (opcional para action_enviar_correo)
SMTP_SERVER = (os.getenv("SMTP_SERVER") or "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
SMTP_USER = (os.getenv("SMTP_USER") or "").strip()
SMTP_PASS = (os.getenv("SMTP_PASS") or "").strip()
EMAIL_FROM = (os.getenv("EMAIL_FROM") or SMTP_USER or "bot@ejemplo.com").strip()

# Timeouts/reintentos para webhooks
REQUEST_TIMEOUT_SECS = int(os.getenv("ACTIONS_HTTP_TIMEOUT", "10"))
MAX_RETRIES = int(os.getenv("ACTIONS_HTTP_RETRIES", "2"))

# Ping opcional en health check
ACTIONS_PING_HELPDESK = (os.getenv("ACTIONS_PING_HELPDESK") or "false").lower() == "true"

# (Opcional) base para links de reset
RESET_URL_BASE = (os.getenv("RESET_URL_BASE") or "https://zajuna.edu").rstrip("/")

# =========================
#   Utilidades HTTP/SMTP
# =========================
def send_email(subject: str, body: str, to_addr: str) -> bool:
    """
    Envía un correo simple por SMTP si hay configuración. Devuelve True/False.
    No lanza excepciones al flujo del bot.
    """
    if not (SMTP_SERVER and SMTP_USER and SMTP_PASS and to_addr):
        logger.info("[actions] SMTP no configurado; omitiendo envío.")
        return False
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = to_addr
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=REQUEST_TIMEOUT_SECS) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, [to_addr], msg.as_string())
        logger.info("[actions] ✅ Correo enviado correctamente.")
        return True
    except Exception as e:
        logger.error("[actions] ❌ Error enviando correo: %s", e)
        return False


def post_json_with_retries(url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Optional[requests.Response]:
    """
    POST JSON con cabeceras y reintento básico.
    Devuelve Response o None si falla definitivamente.
    """
    headers = dict(headers or {})
    headers.setdefault("Content-Type", "application/json")
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_SECS)
            return resp
        except Exception as e:
            logger.warning("[actions] POST intento %s falló: %s", attempt, e)
            if attempt >= MAX_RETRIES + 1:
                break
            time.sleep(0.5 * attempt)
    return None


def _entity_value(tracker: Tracker, name: str) -> Optional[str]:
    """Intenta leer el valor de una entidad por nombre desde el último mensaje."""
    try:
        ents = (tracker.latest_message or {}).get("entities") or []
        for ent in ents:
            if (ent.get("entity") == name) and ("value" in ent):
                return str(ent.get("value") or "").strip()
    except Exception:
        pass
    return None


def _json_payload_from_text(text: str) -> Dict[str, Any]:
    """
    Si el usuario envía algo como: /enviar_soporte{"nombre":"X","email":"Y","mensaje":"Z"}
    intenta parsear la parte JSON.
    """
    if not text:
        return {}
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            raw = text[start : end + 1]
            return json.loads(raw)
    except Exception:
        pass
    return {}

# =========================
#   Validaciones de Forms
# =========================
class ValidateSoporteForm(FormValidationAction):
    """Valida los slots del soporte_form: nombre, email, mensaje"""

    def name(self) -> Text:
        return "validate_soporte_form"

    def validate_nombre(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        v = (value or "").strip()
        if len(v) < 3:
            dispatcher.utter_message(text="⚠️ El nombre debe tener al menos 3 caracteres.")
            return {"nombre": None}
        if len(v) > 120:
            dispatcher.utter_message(text="⚠️ El nombre es muy largo. ¿Puedes abreviarlo un poco?")
            return {"nombre": None}
        return {"nombre": v}

    def validate_email(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        v = (value or "").strip()
        if not EMAIL_RE.match(v):
            dispatcher.utter_message(text="📧 Ese email no parece válido. Escribe algo como usuario@dominio.com")
            return {"email": None}
        return {"email": v}

    def validate_mensaje(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        v = (value or "").strip()
        if len(v) < 8:
            dispatcher.utter_message(text="📝 Dame un poco más de detalle del problema (mínimo 8 caracteres).")
            return {"mensaje": None}
        if len(v) > 5000:
            dispatcher.utter_message(text="📝 El mensaje es muy largo. Intenta resumirlo (máx. 5000).")
            return {"mensaje": None}
        return {"mensaje": v}


class ValidateRecoveryForm(FormValidationAction):
    """Valida el slot email del recovery_form (recuperación de contraseña)"""

    def name(self) -> Text:
        return "validate_recovery_form"

    def validate_email(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        v = (value or "").strip()
        if not EMAIL_RE.match(v):
            dispatcher.utter_message(text="📧 Ese email no parece válido. Escribe algo como usuario@dominio.com")
            return {"email": None}
        return {"email": v}

# ==============   Acciones   ==============

class ActionEnviarCorreo(Action):
    """Envía un email de recuperación (opcionalmente por SMTP)"""

    def name(self) -> Text:
        return "action_enviar_correo"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        email = (tracker.get_slot("email") or "").strip()
        if not email:
            dispatcher.utter_message(text="⚠️ No detecté tu correo. Por favor, escríbelo (ej: usuario@ejemplo.com).")
            return []

        reset_link = f"{RESET_URL_BASE}/reset?email={email}"
        body = (
            "Hola,\n\nHas solicitado recuperar tu contraseña.\n"
            f"Usa el siguiente enlace para continuar: {reset_link}\n\n"
            "Si no fuiste tú, ignora este mensaje."
        )
        sent = send_email("Recuperación de contraseña", body, email)
        jlog(logging.INFO, "action_enviar_correo", email=email, sent=bool(sent))
        if sent:
            dispatcher.utter_message(text="📬 Te envié un enlace de recuperación a tu correo.")
        else:
            dispatcher.utter_message(text="ℹ️ Tu solicitud fue registrada. Revisa tu correo más tarde.")
        return []


class ActionEnviarSoporte(Action):
    """
    Variante genérica para enviar un soporte rápido sin pasar por el form,
    usando datos desde:
      1) Entidades del payload (/enviar_soporte{"nombre":...})
      2) JSON embebido en el texto del último mensaje
      3) Slots existentes
      4) Defaults seguros
    """

    def name(self) -> Text:
        return "action_enviar_soporte"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        # 1) Entities del último mensaje
        nombre_ent = _entity_value(tracker, "nombre")
        email_ent = _entity_value(tracker, "email")
        mensaje_ent = _entity_value(tracker, "mensaje")

        # 2) JSON embebido en el texto (si el canal lo envía así)
        last_text = (tracker.latest_message.get("text") or "").strip()
        json_payload = _json_payload_from_text(last_text)

        # 3) Slots existentes
        nombre_slot = (tracker.get_slot("nombre") or "").strip()
        email_slot = (tracker.get_slot("email") or "").strip()
        mensaje_slot = (tracker.get_slot("mensaje") or "").strip()

        # Resolución por precedencia
        nombre = (nombre_ent or json_payload.get("nombre") or nombre_slot or "Usuario").strip()
        email = (email_ent or json_payload.get("email") or email_slot or "sin-correo@zajuna.edu").strip()
        mensaje = (mensaje_ent or json_payload.get("mensaje") or mensaje_slot or "").strip()
        if not mensaje:
            # Fallback: usa el último texto, pero sin el prefijo intent si viene crudo
            mensaje = last_text if not last_text.startswith("/enviar_soporte") else "Solicitud de soporte (sin detalle)."

        # Saneos mínimos
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
            "name": nombre,
            "email": email,
            "subject": "Soporte rápido (Rasa)",
            "message": mensaje or "Solicitud de soporte (sin detalle).",
            "conversation_id": tracker.sender_id,
            "metadata": meta,
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
    """
    Envía la solicitud del soporte_form al webhook del Helpdesk.
    Variables:
      - HELPDESK_WEBHOOK (URL)
      - HELPDESK_TOKEN   (Bearer opcional)
    """

    def name(self) -> Text:
        return "action_soporte_submit"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
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
            "name": nombre,
            "email": email,
            "subject": "Soporte técnico (Rasa)",
            "message": mensaje,
            "conversation_id": tracker.sender_id,
            "metadata": meta,
        }

        headers = {"Content-Type": "application/json"}
        if HELPDESK_TOKEN:
            headers["Authorization"] = f"Bearer {HELPDESK_TOKEN}"

        resp = post_json_with_retries(HELPDESK_WEBHOOK, payload, headers)
        ok = bool(resp and 200 <= resp.status_code < 300)
        jlog(logging.INFO, "action_soporte_submit", ok=ok, status_code=getattr(resp, "status_code", None))
        if ok:
            data: Dict[str, Any] = {}
            try:
                data = resp.json()
            except Exception:
                pass
            tid = (data or {}).get("ticket_id") or (data or {}).get("id")
            if tid:
                dispatcher.utter_message(text=f"🎫 Ticket creado correctamente. ID: {tid}")
            else:
                dispatcher.utter_message(response="utter_soporte_creado")
            # limpiar slots del form
            return [SlotSet("nombre", None), SlotSet("email", None), SlotSet("mensaje", None)]
        else:
            code = getattr(resp, "status_code", "sin-respuesta")
            logger.error("[actions] Helpdesk respondió %s: %s", code, getattr(resp, "text", ""))
            dispatcher.utter_message(response="utter_soporte_error")
            return []


class ActionConectarHumano(Action):
    """Crea ticket de 'escalado a humano' por el mismo webhook genérico."""

    def name(self) -> Text:
        return "action_conectar_humano"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        nombre = (tracker.get_slot("nombre") or "Estudiante").strip()
        email = (tracker.get_slot("email") or "sin-correo@zajuna.edu").strip()
        last_user_msg = tracker.latest_message.get("text") or "El usuario solicitó ser atendido por un humano."

        contexto = {
            "conversation_id": tracker.sender_id,
            "last_message": last_user_msg,
            "slots": tracker.current_slot_values(),
            "latest_intent": (tracker.latest_message.get("intent") or {}).get("name"),
            "timestamp": int(time.time()),
            "metadata": (tracker.latest_message or {}).get("metadata") or {},
        }

        payload = {
            "name": nombre,
            "email": email,
            "subject": "Escalada a humano desde el chatbot",
            "message": last_user_msg,
            "conversation_id": tracker.sender_id,
            "metadata": contexto,
        }

        headers = {"Content-Type": "application/json"}
        if HELPDESK_TOKEN:
            headers["Authorization"] = f"Bearer {HELPDESK_TOKEN}"

        resp = post_json_with_retries(HELPDESK_WEBHOOK, payload, headers)
        ok = bool(resp and 200 <= resp.status_code < 300)
        jlog(logging.INFO, "action_conectar_humano", ok=ok, status_code=getattr(resp, "status_code", None))
        if ok:
            dispatcher.utter_message(text="🧑‍💻 ¡Listo! Te conecto con un agente humano, por favor espera…")
        else:
            code = getattr(resp, "status_code", "sin-respuesta")
            logger.error("[actions] Escalado falló %s: %s", code, getattr(resp, "text", ""))
            dispatcher.utter_message(text="⚠️ No pude crear el ticket de escalado en este momento.")
        return []


class ActionHealthCheck(Action):
    """
    Health-check ligero del servidor de acciones y, opcionalmente,
    del webhook de Helpdesk (ACTIONS_PING_HELPDESK=true).
    No requiere modificar stories; puedes invocarlo manualmente si lo necesitas.
    """

    def name(self) -> Text:
        return "action_health_check"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        status: Dict[str, Any] = {"actions": "ok"}
        if ACTIONS_PING_HELPDESK:
            try:
                r = requests.options(HELPDESK_WEBHOOK, timeout=3)
                status["helpdesk"] = f"ok ({r.status_code})"
            except Exception as e:
                status["helpdesk"] = f"error: {e}"
        else:
            status["helpdesk"] = "skip"

        jlog(logging.INFO, "action_health_check", **status)
        # Mensaje simple para ver en UI/logs
        dispatcher.utter_message(text=f"health: {json.dumps(status, ensure_ascii=False)}")
        return []

# =========================
#        Auth gating
# =========================
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")

def _has_auth(tracker: Tracker) -> bool:
    """Devuelve True si la UI/proxy indicó que hay auth válida."""
    meta = (tracker.latest_message or {}).get("metadata") or {}
    auth = meta.get("auth") if isinstance(meta, dict) else {}

    # Caso simple enviado por la UI: metadata.auth.hasToken = true|false
    if isinstance(auth, dict) and auth.get("hasToken"):
        return True

    # Si tu proxy añade claims tras validar JWT en FastAPI
    if isinstance(auth, dict) and auth.get("claims"):
        return True

    # (Opcional) Validación local del JWT si decidieras pasar el token crudo.
    # token = isinstance(auth, dict) and auth.get("token")
    # if token and JWT_PUBLIC_KEY:
    #     try:
    #         import jwt  # pyjwt
    #         jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[JWT_ALGORITHM], options={"verify_aud": False})
    #         return True
    #     except Exception:
    #         return False

    return False


class ActionCheckAuth(Action):
    def name(self) -> Text:
        return "action_check_auth"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:
        intent = ((tracker.latest_message or {}).get("intent") or {}).get("name") or ""
        authed = _has_auth(tracker)

        if intent in ("estado_estudiante", "ver_certificados"):
            if not authed:
                # ChatUI reconocerá custom.type=auth_needed y mostrará botón "Iniciar sesión"
                dispatcher.utter_message(response="utter_need_auth")
                return []

            # Con auth válida: responde (o delega a otra action que consulte tu API)
            if intent == "estado_estudiante":
                dispatcher.utter_message(response="utter_estado_estudiante")
            elif intent == "ver_certificados":
                dispatcher.utter_message(response="utter_certificados_info")
            return []

        # Otros intents: no interviene
        return []
