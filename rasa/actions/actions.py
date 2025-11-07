# rasa/actions/actions.py
from __future__ import annotations

import os
import re
import time
import json
import smtplib
import logging
import datetime
from typing import Any, Dict, List, Optional, Text

import requests
from email.mime.text import MIMEText

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType, FollowupAction
from rasa_sdk.types import DomainDict
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import SlotSet
from rasa_sdk.events import SlotSet, ConversationPaused
from .acciones_encuesta import ActionRegistrarEncuesta
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ConversationPaused, ConversationResumed
from datetime import datetime
from actions.acciones_sesion_segura import *
from utils.mongo_autosave import guardar_autosave, obtener_autosave, limpiar_autosave, actualizar_campo
__all__ = [
    # Validators
    "ValidateSoporteForm",
    "ValidateRecoveryForm",

    # Core utility / email
    "ActionEnviarCorreo",

    # Soporte
    "ActionEnviarSoporte",
    "ActionSoporteSubmit",
    "ActionSubmitSoporte",

    # Humano / health
    "ActionConectarHumano",
    "ActionHealthCheck",

    # Auth / gates y sync
    "ActionCheckAuth",
    "ActionCheckAuthEstado",
    "ActionSyncAuthFromMetadata",
    "ActionSetAuthenticatedTrue",
    "ActionMarkAuthenticated",

    # Flujos académicos
    "ActionEstadoEstudiante",
    "ActionVerCertificados",
    "ActionListarCertificados",
    "ActionTutorAsignado",

    # Recovery
    "ActionSubmitRecovery",

    # Encuesta / resolución / desvío
    "ActionPreguntarResolucion",
    "ActionDerivarYRegistrarHumano",
    "ActionRegistrarEncuesta",
    "ActionOfrecerContinuarTema",
    "ActionIngresoZajuna",
    "ActionRecuperarContrasena",
    "ActionNecesitaAuth",
    "ActionSetEncuestaTipo",
    "ActionSetMenuPrincipal"

    
    "ActionFinalizarConversacion",
    "ActionCancelarCierre",
    "ActionVerificarProcesoActivo",
    "ActionConfirmarCierre",
   
    "ActionVerificarProcesoActivoAutosave",
    "ActionGuardarEncuestaIncompleta",
    "ActionConfirmarCierreAutosave",

    "ActionVerificarEstadoConversacion",
    "ActionGuardarProgresoConversacion",
    "ActionTerminarConversacionSegura",
    "ActionReanudarConversacionSegura",
    "ActionAutoResume",
    "ActionReanudarAuto"

    "ActionOfrecerContinuarTema",
    "ActionConfirmarCierreSeguro",
    "ActionAutoSaveEncuesta",
    "ActionGuardarAutoSaveMongo",
    "ActionCargarAutoSaveMongo",
    "ActionAutoResumeConversacion",
    "ActionResetConversacionSegura",

   "ActionNotificarDesconexion",
   "ActionNotificarInactividad",
   "ActionNotificarReconexion",
   "ActionGuardarEstadoSeguridad",
   "ActionRecuperarEstadoSeguridad",

   "ActionGuardianGuardarProgreso",
   "ActionGuardianCargarProgreso",
   "ActionGuardianPausar",
   "ActionGuardianReanudar",
   "ActionGuardianReset"

   "ActionGuardianGuardarProgreso",
   "ActionGuardianCargarProgreso",
   "ActionGuardianPausar",
   "ActionGuardianReanudar",
   "ActionGuardianReset",
   "ActionRegistrarEncuesta",

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
    """Envía un correo simple por SMTP si hay configuración. Devuelve True/False."""
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
    """POST JSON con cabeceras y reintento básico. Devuelve Response o None si falla definitivamente."""
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

# --------- Helpers reutilizables ---------
def _is_auth(tracker: Tracker) -> bool:
    return bool(tracker.get_slot("is_authenticated"))

def _backend_base() -> str:
    return (os.getenv("BACKEND_URL") or "").rstrip("/")

def _auth_headers(tracker: Tracker) -> Dict[str, str]:
    token = tracker.get_slot("auth_token")
    return {"Authorization": f"Bearer {token}"} if token else {}

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
    ) -> List[EventType]:
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
    ) -> List[EventType]:
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
    """Envía la solicitud del soporte_form al webhook del Helpdesk."""

    def name(self) -> Text:
        return "action_soporte_submit"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
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
            return [SlotSet("nombre", None), SlotSet("email", None), SlotSet("mensaje", None)]
        else:
            code = getattr(resp, "status_code", "sin-respuesta")
            logger.error("[actions] Helpdesk respondió %s: %s", code, getattr(resp, "text", ""))
            dispatcher.utter_message(response="utter_soporte_error")
            return []

class ActionSubmitSoporte(Action):
    """Alias retrocompatible: mantiene el nombre antiguo y delega en ActionSoporteSubmit."""

    def name(self) -> Text:
        return "action_submit_soporte"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        return ActionSoporteSubmit().run(dispatcher, tracker, domain)

class ActionConectarHumano(Action):
    """Crea ticket de 'escalado a humano' por el mismo webhook genérico."""

    def name(self) -> Text:
        return "action_conectar_humano"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
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
    """Health-check ligero del servidor de acciones y, opcionalmente, del webhook de Helpdesk."""

    def name(self) -> Text:
        return "action_health_check"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
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

    if isinstance(auth, dict) and auth.get("hasToken"):
        return True
    if isinstance(auth, dict) and auth.get("claims"):
        return True
    return False

class ActionCheckAuth(Action):
    def name(self) -> Text:
        return "action_check_auth"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[EventType]:
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

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[EventType]:
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

# --------- Flujos académicos ---------
class ActionEstadoEstudiante(Action):
    def name(self) -> Text:
        return "action_estado_estudiante"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        # 1) Gate de autenticación
        if not _is_auth(tracker):
            dispatcher.utter_message(response="utter_need_auth")
            return []

        # 2) Backend opcional
        estado: Optional[str] = None
        base = _backend_base()
        if base:
            try:
                resp = requests.get(f"{base}/api/estado-estudiante", headers=_auth_headers(tracker), timeout=8)
                if resp.ok:
                    data = resp.json()
                    estado = data.get("estado") if isinstance(data, dict) else None
            except Exception:
                pass

        # 3) Fallback demo
        if not estado:
            estado = "Activo (demo)"

        dispatcher.utter_message(text=f"✅ Tu estado académico es: {estado}.")
        return []

class ActionTutorAsignado(Action):
    def name(self) -> Text:
        return "action_tutor_asignado"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict]:
        if not _is_auth(tracker):
            dispatcher.utter_message(response="utter_need_auth")
            return []

        base = _backend_base()
        tutor_nombre: Optional[str] = None
        tutor_contacto: Optional[str] = None

        if base:
            try:
                resp = requests.get(f"{base}/api/tutor", headers=_auth_headers(tracker), timeout=8)
                if resp.ok:
                    data = resp.json() if isinstance(resp.json(), dict) else {}
                    tutor_nombre = data.get("nombre")
                    tutor_contacto = data.get("contacto")
            except Exception:
                pass

        if not tutor_nombre:
            tutor_nombre = "Ing. María Pérez (demo)"
        if not tutor_contacto:
            tutor_contacto = "maria.perez@zajuna.edu (demo)"

        dispatcher.utter_message(text=f"👩‍🏫 Tu tutor asignado es {tutor_nombre}. Contacto: {tutor_contacto}.")
        return []

class ActionListarCertificados(Action):
    def name(self) -> Text:
        return "action_listar_certificados"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        is_auth = bool(tracker.get_slot("is_authenticated"))
        if not is_auth:
            dispatcher.utter_message(response="utter_need_auth")
            return []

        base_url = (os.getenv("BACKEND_URL") or "").rstrip("/")
        certificados: Optional[List[Dict[str, Any]]] = None

        if base_url:
            try:
                token = tracker.get_slot("auth_token")
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                resp = requests.get(f"{base_url}/api/certificados", headers=headers, timeout=8)
                if resp.ok:
                    data = resp.json()
                    certificados = data.get("certificados") if isinstance(data, dict) else data
            except Exception:
                pass

        if not certificados:
            certificados = [
                {"curso": "Excel Intermedio", "fecha": "2025-06-10", "url": "https://zajuna.example/cert/123"},
                {"curso": "Programación Básica", "fecha": "2025-04-02", "url": "https://zajuna.example/cert/456"},
            ]

        lines = []
        for item in certificados:
            curso = item.get("curso", "Certificado")
            fecha = item.get("fecha", "s.f.")
            url = item.get("url")
            lines.append(f"• {curso} ({fecha})" + (f" → {url}" if url else ""))

        dispatcher.utter_message(text="🧾 Tus certificados:\n" + "\n".join(lines))
        return []

class ActionVerCertificados(Action):
    def name(self) -> Text:
        return "action_ver_certificados"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict]:
        if not _is_auth(tracker):
            dispatcher.utter_message(response="utter_need_auth")
            return []

        base = _backend_base()
        certificados: Optional[List[Dict[str, Any]]] = None
        if base:
            try:
                resp = requests.get(f"{base}/api/certificados", headers=_auth_headers(tracker), timeout=8)
                if resp.ok:
                    data = resp.json()
                    certificados = data.get("certificados") if isinstance(data, dict) else data
            except Exception:
                pass

        if not certificados:
            certificados = [
                {"curso": "Excel Intermedio", "fecha": "2025-06-10", "url": "https://zajuna.example/cert/123"},
                {"curso": "Programación Básica", "fecha": "2025-04-02", "url": "https://zajuna.example/cert/456"},
            ]

        lines = []
        for item in certificados:
            curso = item.get("curso", "Certificado")
            fecha = item.get("fecha", "s.f.")
            url = item.get("url")
            lines.append(f"• {curso} ({fecha})" + (f" → {url}" if url else ""))

        dispatcher.utter_message(text="🧾 Tus certificados:\n" + "\n".join(lines))
        return []

# --------- Auth helpers / recovery ---------
class ActionCheckAuthEstado(Action):
    def name(self) -> Text:
        return "action_check_auth_estado"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[EventType]:
        meta = (tracker.latest_message or {}).get("metadata") or {}
        has_token = bool(((meta.get("auth") or {}).get("hasToken")))
        if has_token:
            return [FollowupAction("action_estado_estudiante")]
        else:
            return [FollowupAction("utter_need_auth")]

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

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        return [SlotSet("is_authenticated", True)]

class ActionMarkAuthenticated(Action):
    def name(self):
        return "action_mark_authenticated"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("is_authenticated", True)]

# --------- Encuesta / resolución / desvío ---------
class ActionPreguntarResolucion(Action):
    def name(self) -> Text:
        return "action_preguntar_resolucion"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(response="utter_esta_resuelto")
        return []

class ActionDerivarYRegistrarHumano(Action):
    def name(self) -> Text:
        return "action_derivar_y_registrar_humano"

    def run(self, dispatcher, tracker, domain):
        # Aquí crear ticket / enviar correo / registrar en Mongo (cuando quieras)
        return []

class ActionRegistrarEncuesta(Action):
    def name(self) -> Text:
        return "action_registrar_encuesta"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        satisfaccion = tracker.latest_message.get('intent', {}).get('name', 'desconocido')
        comentario = tracker.latest_message.get('text', 'sin comentario')
        usuario = tracker.get_slot("usuario") or "anónimo"
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        registro = {
            "usuario": usuario,
            "satisfaccion": satisfaccion,
            "comentario": comentario,
            "fecha": fecha
        }

        ruta = "data/encuestas.json"
        os.makedirs("data", exist_ok=True)
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")

        dispatcher.utter_message(text="✅ Registro de satisfacción guardado correctamente.")
        return []

class ActionOfrecerContinuarTema(Action):
    def name(self) -> Text:
        return "action_ofrecer_continuar_tema"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_ofrecer_continuar")
        return []
class ActionIngresoZajuna(Action):
    def name(self) -> str:
        return "action_ingreso_zajuna"

    async def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Perfecto, vamos a iniciar sesión. Por favor ingresa tus credenciales.")
        return []

class ActionIngresoZajuna(Action):
    def name(self) -> str:
        return "action_ingreso_zajuna"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: dict) -> list:
        dispatcher.utter_message(text="Perfecto, vamos a iniciar sesión. Por favor ingresa tus credenciales.")
        return []

class ActionRecuperarContrasena(Action):
    def name(self) -> str:
        return "action_recuperar_contrasena"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: dict) -> list:
        dispatcher.utter_message(text="No hay problema. Te ayudaré a recuperar tu contraseña. Por favor sigue el enlace que te enviaré.")
        return []

class ActionNecesitaAuth(Action):
    def name(self) -> str:
        return "action_necesita_auth"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: dict) -> list:
        dispatcher.utter_message(text="Para continuar con esta acción necesitas iniciar sesión. ¿Deseas hacerlo ahora?")
        return []

class ActionSetEncuestaTipo(Action):
    def name(self):
        return "action_set_encuesta_tipo"

    def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message['intent'].get('name')
        
        encuesta_tipo = None
        if intent == "respuesta_satisfecho":
            # Lógica de flujo para positiva
            # Puedes personalizar según tu intención
            encuesta_tipo = "continuar"  # o "finaliza"
        elif intent == "respuesta_insatisfecho":
            # Lógica de flujo para negativa
            encuesta_tipo = "contacto_tutor"  # o "directo"
        
        return [SlotSet("encuesta_tipo", encuesta_tipo)]
class ActionSetMenuPrincipal(Action):
    def name(self) -> Text:
        return "action_set_menu_principal"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        return [SlotSet("menu_actual", "principal")]

class ActionVerEstadoEstudiante(Action):
    def name(self) -> Text:
        return "action_ver_estado_estudiante"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if tracker.get_slot("is_authenticated"):
            dispatcher.utter_message(text="Aquí está tu estado como estudiante...")
        else:
            dispatcher.utter_message(response="utter_login_requerido")

        return []

class ActionConsultarCertificados(Action):
    def name(self) -> Text:
        return "action_consultar_certificados"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if tracker.get_slot("is_authenticated"):
            dispatcher.utter_message(text="Aquí tienes tus certificados disponibles...")
        else:
            dispatcher.utter_message(response="utter_login_requerido")

        return []
class ActionConfirmarCierre(Action):
    def name(self) -> Text:
        return "action_confirmar_cierre"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_confirmar_cierre")
        return [SlotSet("confirmacion_cierre", "pendiente")]


class ActionFinalizarConversacion(Action):
    def name(self) -> Text:
        return "action_finalizar_conversacion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_despedida_final")
        return [
            SlotSet("session_activa", False),
            SlotSet("confirmacion_cierre", None),
            ConversationPaused()
        ]


class ActionCancelarCierre(Action):
    def name(self) -> Text:
        return "action_cancelar_cierre"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_cancelar_cierre")
        return [
            SlotSet("confirmacion_cierre", None),
            ConversationResumed()
        ]
class ActionVerificarProcesoActivo(Action):
    def name(self) -> Text:
        return "action_verificar_proceso_activo"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        proceso_activo = tracker.get_slot("proceso_activo")
        if proceso_activo:
            dispatcher.utter_message(response="utter_confirmar_cierre_seguro")
            return [SlotSet("confirmacion_cierre", "pendiente")]
        else:
            dispatcher.utter_message(response="utter_confirmar_cierre")
            return [SlotSet("confirmacion_cierre", "pendiente")]


class ActionConfirmarCierre(Action):
    def name(self) -> Text:
        return "action_confirmar_cierre"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_despedida_final")
        return [
            SlotSet("session_activa", False),
            SlotSet("confirmacion_cierre", None),
            SlotSet("proceso_activo", None),
            ConversationPaused()
        ]


class ActionCancelarCierre(Action):
    def name(self) -> Text:
        return "action_cancelar_cierre"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_cancelar_cierre")
        return [
            SlotSet("confirmacion_cierre", None),
            ConversationResumed()
        ]
class ActionVerificarProcesoActivoAutosave(Action):
    def name(self) -> Text:
        return "action_verificar_proceso_activo_autosave"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        proceso_activo = tracker.get_slot("proceso_activo")
        encuesta_incompleta = tracker.get_slot("encuesta_incompleta")

        if encuesta_incompleta:
            dispatcher.utter_message(response="utter_confirmar_cierre_con_autosave")
            return [SlotSet("confirmacion_cierre", "pendiente")]
        elif proceso_activo:
            dispatcher.utter_message(response="utter_confirmar_cierre_seguro")
            return [SlotSet("confirmacion_cierre", "pendiente")]
        else:
            dispatcher.utter_message(response="utter_confirmar_cierre")
            return [SlotSet("confirmacion_cierre", "pendiente")]


class ActionGuardarEncuestaIncompleta(Action):
    def name(self) -> Text:
        return "action_guardar_encuesta_incompleta"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Simulación de guardado parcial (integración con ActionRegistrarEncuesta)
        usuario = tracker.sender_id
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        dispatcher.utter_message(
            text=f"Guardando tu progreso de encuesta ({fecha}) para el usuario {usuario}..."
        )
        dispatcher.utter_message(text="✅ Encuesta parcial registrada correctamente.")

        return [
            SlotSet("encuesta_incompleta", False),
            SlotSet("proceso_activo", None)
        ]


class ActionConfirmarCierreAutosave(Action):
    def name(self) -> Text:
        return "action_confirmar_cierre_autosave"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        encuesta_incompleta = tracker.get_slot("encuesta_incompleta")

        if encuesta_incompleta:
            # Guardar antes de cerrar
            dispatcher.utter_message(response="utter_despedida_final")
            return [
                SlotSet("session_activa", False),
                SlotSet("confirmacion_cierre", None),
                SlotSet("encuesta_incompleta", False),
                ConversationPaused()
            ]
        else:
            dispatcher.utter_message(response="utter_despedida_sin_guardar")
            return [
                SlotSet("session_activa", False),
                SlotSet("confirmacion_cierre", None),
                ConversationPaused()
            ]


class ActionCancelarCierre(Action):
    def name(self) -> Text:
        return "action_cancelar_cierre"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_cancelar_cierre")
        return [
            SlotSet("confirmacion_cierre", None),
            ConversationResumed()
        ]
class ActionVerificarEstadoEncuesta(Action):
    def name(self) -> Text:
        return "action_verificar_estado_encuesta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        encuesta_activa = tracker.get_slot("encuesta_activa")
        if encuesta_activa:
            dispatcher.utter_message(response="utter_confirmar_cierre")
        else:
            dispatcher.utter_message(response="utter_cierre_confirmado")
            return [ConversationPaused()]
        return []

class ActionGuardarProgresoEncuesta(Action):
    def name(self) -> Text:
        return "action_guardar_progreso_encuesta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(response="utter_guardando_progreso")

        # 🔗 Conecta con ActionRegistrarEncuesta para persistencia real
        encuesta_data = {
            "usuario": tracker.sender_id,
            "estado": "pendiente",
            "tipo": tracker.get_slot("encuesta_activa"),
            "comentario": tracker.latest_message.get("text")
        }
        ActionRegistrarEncuesta().registrar_en_base(encuesta_data)

        return [SlotSet("encuesta_activa", False)]

class ActionTerminarConversacionSegura(Action):
    def name(self) -> Text:
        return "action_terminar_conversacion_segura"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        encuesta_activa = tracker.get_slot("encuesta_activa")

        if encuesta_activa:
            return [SlotSet("encuesta_activa", True)]
        else:
            dispatcher.utter_message(response="utter_cierre_confirmado")
            return [ConversationPaused()]


class ActionIrMenuPrincipal(Action):
    def name(self) -> Text:
        return "action_ir_menu_principal"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(response="utter_menu_principal")
        return []

class ActionAutoResume(Action):
    def name(self) -> Text:
        return "action_auto_resume"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        encuesta_activa = tracker.get_slot("encuesta_activa")
        usuario = tracker.sender_id

        if encuesta_activa:
            dispatcher.utter_message(
                text=f"👋 Hola {usuario}, parece que dejaste una encuesta sin terminar. ¿Deseas continuar?"
            )
            return [SlotSet("reanudar_pendiente", True)]
        else:
            dispatcher.utter_message(text="👋 ¡Hola! Bienvenido de nuevo. No tienes tareas pendientes.")
            return [SlotSet("reanudar_pendiente", False)]


class ActionReanudarAuto(Action):
    def name(self) -> Text:
        return "action_reanudar_auto"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        if tracker.get_slot("reanudar_pendiente"):
            dispatcher.utter_message(
                text="🔄 Retomando tu encuesta o proceso pendiente donde lo dejaste..."
            )
            return [ConversationResumed()]
        else:
            dispatcher.utter_message(text="Nada pendiente. Continuemos desde el inicio.")
            return []
class ActionConfirmarCierreSeguro(Action):
    def name(self):
        return "action_confirmar_cierre_seguro"

    def run(self, dispatcher, tracker, domain):
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(response="utter_confirmar_cierre")
        else:
            dispatcher.utter_message(response="utter_cierre_confirmado")
            return [ConversationPaused()]
        return []


class ActionAutoSaveEncuesta(Action):
    def name(self):
        return "action_autosave_encuesta"

    def run(self, dispatcher, tracker, domain):
        datos = tracker.current_slot_values()
        autosave_collection.update_one(
            {"user_id": tracker.sender_id},
            {"$set": {"slots": datos, "estado": "guardado"}},
            upsert=True
        )
        dispatcher.utter_message(text="Progreso guardado automáticamente 🧠")
        return []


class ActionGuardarAutoSaveMongo(Action):
    def name(self):
        return "action_guardar_autosave_mongo"

    def run(self, dispatcher, tracker, domain):
        data = {"user_id": tracker.sender_id, "slots": tracker.current_slot_values()}
        autosave_collection.update_one({"user_id": tracker.sender_id}, {"$set": data}, upsert=True)
        dispatcher.utter_message(text="Datos guardados en MongoDB 🗄️")
        return []


class ActionCargarAutoSaveMongo(Action):
    def name(self):
        return "action_cargar_autosave_mongo"

    def run(self, dispatcher, tracker, domain):
        registro = autosave_collection.find_one({"user_id": tracker.sender_id})
        if registro and "slots" in registro:
            dispatcher.utter_message(text="Cargando tus datos previos...")
            return [SlotSet(k, v) for k, v in registro["slots"].items()]
        else:
            dispatcher.utter_message(text="No se encontró información guardada previa.")
        return []


class ActionAutoResumeConversacion(Action):
    def name(self):
        return "action_autoresume_conversacion"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="He restaurado tu conversación anterior. Puedes continuar.")
        return [ConversationResumed()]


class ActionResetConversacionSegura(Action):
    def name(self):
        return "action_reset_conversacion_segura"

    def run(self, dispatcher, tracker, domain):
        autosave_collection.delete_one({"user_id": tracker.sender_id})
        dispatcher.utter_message(text="Datos temporales eliminados correctamente. ✅")
        return [SlotSet("encuesta_activa", False), SlotSet("autosave_estado", None)]





# --------- Flujo de cierre/pausa segura ---------
class ActionVerificarEstadoConversacion(Action):
    def name(self) -> Text:
        return "action_verificar_estado_conversacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        encuesta_activa = tracker.get_slot("encuesta_activa")
        if encuesta_activa:
            dispatcher.utter_message(response="utter_confirmar_cierre")
            return []
        else:
            dispatcher.utter_message(response="utter_cierre_confirmado")
            return [ConversationPaused()]

class ActionGuardarProgresoConversacion(Action):
    def name(self) -> Text:
        return "action_guardar_progreso_conversacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        dispatcher.utter_message(response="utter_guardando_progreso")
        encuesta_data = {
            "usuario": tracker.sender_id,
            "estado": "incompleta",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "tipo": tracker.get_slot("encuesta_activa"),
            "comentario": (tracker.latest_message or {}).get("text", ""),
            "slots": tracker.current_slot_values(),
        }
        guardar_autosave(tracker.sender_id, encuesta_data, estado="incompleta")
        dispatcher.utter_message(text="✅ Progreso guardado correctamente.")
        return [SlotSet("encuesta_activa", True)]

class ActionTerminarConversacionSegura(Action):
    def name(self) -> Text:
        return "action_terminar_conversacion_segura"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(response="utter_confirmar_cierre")
            return []
        dispatcher.utter_message(response="utter_cierre_confirmado")
        return [ConversationPaused()]

class ActionReanudarConversacionSegura(Action):
    def name(self) -> Text:
        return "action_reanudar_conversacion_segura"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(text="🔄 Retomamos tu encuesta o proceso pendiente donde lo dejaste.")
            return [ConversationResumed()]
        dispatcher.utter_message(text="No había nada pendiente, puedes continuar normalmente.")
        return []

class ActionConfirmarCierreSeguro(Action):
    def name(self) -> Text:
        return "action_confirmar_cierre_seguro"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(response="utter_confirmar_cierre")
            return []
        dispatcher.utter_message(response="utter_cierre_confirmado")
        return [ConversationPaused()]

# --------- Autosave genérico ---------
class ActionAutoSaveEncuesta(Action):
    def name(self) -> Text:
        return "action_autosave_encuesta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        datos = tracker.current_slot_values()
        guardar_autosave(tracker.sender_id, {"slots": datos}, estado="guardado")
        dispatcher.utter_message(text="🧠 Progreso guardado automáticamente.")
        return []

class ActionGuardarAutoSaveMongo(Action):
    def name(self) -> Text:
        return "action_guardar_autosave_mongo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        guardar_autosave(tracker.sender_id, {"slots": tracker.current_slot_values()}, estado="guardado")
        dispatcher.utter_message(text="🗄️ Datos guardados en MongoDB.")
        return []

class ActionCargarAutoSaveMongo(Action):
    def name(self) -> Text:
        return "action_cargar_autosave_mongo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        registro = obtener_autosave(tracker.sender_id)
        if registro and "slots" in registro:
            dispatcher.utter_message(text="Cargando tus datos previos...")
            return [SlotSet(k, v) for k, v in (registro["slots"] or {}).items()]
        dispatcher.utter_message(text="No se encontró información guardada previa.")
        return []

class ActionAutoResumeConversacion(Action):
    def name(self) -> Text:
        return "action_autoresume_conversacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        dispatcher.utter_message(text="He restaurado tu conversación anterior. Puedes continuar.")
        return [ConversationResumed()]

class ActionResetConversacionSegura(Action):
    def name(self) -> Text:
        return "action_reset_conversacion_segura"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        limpiar_autosave(tracker.sender_id)
        dispatcher.utter_message(text="🧹 Datos temporales eliminados correctamente.")
        return [SlotSet("encuesta_activa", False), SlotSet("autosave_estado", None)]

# --------- Eventos de seguridad (desconexión/inactividad/reconexión) ---------
class ActionNotificarDesconexion(Action):
    def name(self) -> Text:
        return "action_notificar_desconexion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        dispatcher.utter_message(response="utter_notificar_desconexion")
        actualizar_campo(
            tracker.sender_id,
            evento="desconexion",
            slots=tracker.current_slot_values(),
        )
        return [SlotSet("evento_seguridad", "desconexion")]

class ActionNotificarInactividad(Action):
    def name(self) -> Text:
        return "action_notificar_inactividad"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        dispatcher.utter_message(response="utter_notificar_inactividad")
        actualizar_campo(
            tracker.sender_id,
            evento="inactividad",
            slots=tracker.current_slot_values(),
        )
        return [SlotSet("evento_seguridad", "inactividad")]

class ActionNotificarReconexion(Action):
    def name(self) -> Text:
        return "action_notificar_reconexion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        dispatcher.utter_message(response="utter_notificar_reconexion")
        registro = obtener_autosave(tracker.sender_id)
        if registro and "slots" in registro:
            return [SlotSet(k, v) for k, v in (registro["slots"] or {}).items()]
        return []

class ActionGuardarEstadoSeguridad(Action):
    def name(self) -> Text:
        return "action_guardar_estado_seguridad"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        actualizar_campo(
            tracker.sender_id,
            evento=tracker.get_slot("evento_seguridad"),
            slots=tracker.current_slot_values(),
        )
        dispatcher.utter_message(text="💾 Estado de seguridad guardado.")
        return []

class ActionRecuperarEstadoSeguridad(Action):
    def name(self) -> Text:
        return "action_recuperar_estado_seguridad"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        registro = obtener_autosave(tracker.sender_id)
        if registro and "slots" in registro:
            dispatcher.utter_message(text="🔄 Restaurando sesión guardada...")
            return [SlotSet(k, v) for k, v in (registro["slots"] or {}).items()]
        dispatcher.utter_message(text="No se encontró sesión guardada previa.")
        return []