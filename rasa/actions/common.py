# ruta: rasa/actions/common.py
from __future__ import annotations

import json
import logging
import os
import re
import smtplib
import time
from email.mime.text import MIMEText
from typing import Any, Optional, Text

import requests
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

# ================================================================
# LOGGING CONFIGURATION
# ================================================================

logger = logging.getLogger("rasa.actions")

if not logger.hasHandlers():
    level = os.getenv("ACTIONS_LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level, logging.INFO))

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logger.addHandler(handler)


def jlog(level: int, event: str, **data: Any) -> None:
    """Logs estructurados en formato JSON con fallback seguro a string."""
    try:
        logger.log(
            level,
            json.dumps(
                {
                    "event": event,
                    **data,
                },
                ensure_ascii=False,
            ),
        )
    except Exception:
        logger.log(level, "%s %s", event, data)


# ================================================================
# GLOBAL CONFIGURATION & ENVIRONMENT VARIABLES
# ================================================================

BACKEND_URL = os.getenv("BACKEND_URL", "").rstrip("/")
RESET_URL_BASE = os.getenv("RESET_URL_BASE", "https://zajuna.edu").rstrip("/")

try:
    REQUEST_TIMEOUT = int(os.getenv("ACTIONS_HTTP_TIMEOUT", "10"))
except ValueError:
    REQUEST_TIMEOUT = 10

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

ACTIONS_PING_HELPDESK = os.getenv("ACTIONS_PING_HELPDESK", "false").lower() == "true"
HELPDESK_WEBHOOK = os.getenv("HELPDESK_WEBHOOK", "")
HELPDESK_TOKEN = os.getenv("HELPDESK_TOKEN", "")

if not HELPDESK_TOKEN:
    logger.error("[ERROR] CRÍTICO: La variable de entorno 'HELPDESK_TOKEN' no está configurada.")


# ================================================================
# AUTHENTICATION HELPERS
# ================================================================

def is_authenticated(tracker: Tracker) -> bool:
    """Verifica si el usuario actual cuenta con una sesión válida en el bot."""
    meta = (tracker.latest_message or {}).get("metadata") or {}

    return bool(
        tracker.get_slot("is_authenticated")
        or tracker.get_slot("auth_token")
        or (isinstance(meta, dict) and meta.get("auth"))
    )


# ----------------------------------------------------------------
# Compatibilidad temporal (Mantenidos para evitar breaking changes)
# ----------------------------------------------------------------
def _is_auth(tracker: Tracker) -> bool:
    return is_authenticated(tracker)


def _has_auth(tracker: Tracker) -> bool:
    return is_authenticated(tracker)


def auth_headers(tracker: Tracker) -> dict[str, str]:
    """Genera las cabeceras HTTP de autorización Bearer si el token existe."""
    token = (tracker.get_slot("auth_token") or "").strip()
    return {"Authorization": f"Bearer {token}"} if token else {}


# ================================================================
# CONTEXT EXTRACTORS
# ================================================================

def get_user_context(tracker: Tracker) -> dict[str, Any]:
    """Extrae la información de contexto del estudiante inyectada en los metadatos."""
    meta = (tracker.latest_message or {}).get("metadata") or {}
    user = meta.get("user") or {}

    return {
        "mode": user.get("mode"),
        "email": user.get("email"),
        "user_id": user.get("id"),
    }


def get_entity(tracker: Tracker, name: str) -> Optional[str]:
    """Extrae y limpia de manera segura el primer valor de una entidad detectada."""
    for entity in (tracker.latest_message or {}).get("entities") or []:
        if entity.get("entity") == name:
            return str(entity.get("value") or "").strip()
    return None


def _entity_value(tracker: Any, entity_name: Text) -> Optional[Text]:
    """Helper de extracción directa para compatibilidad con acciones_soporte.py."""
    entity = next(tracker.get_latest_entity_values(entity_name), None)
    return str(entity) if entity is not None else None


# ================================================================
# NETWORK & BACKEND INTEGRATIONS
# ================================================================

def backend_get(
    tracker: Tracker,
    endpoint: str,
    timeout: Optional[int] = None,
) -> Optional[dict[str, Any]]:
    """Realiza peticiones GET seguras al backend central de la aplicación."""
    if not BACKEND_URL:
        return None

    try:
        resp = requests.get(
            f"{BACKEND_URL}{endpoint}",
            headers=auth_headers(tracker),
            timeout=timeout or REQUEST_TIMEOUT,
        )

        if not resp.ok:
            logger.warning("[BACKEND] status=%s endpoint=%s", resp.status_code, endpoint)
            return None

        try:
            return resp.json()
        except ValueError:
            logger.error("[BACKEND] invalid json: %s", endpoint)
            return None

    except requests.RequestException:
        logger.exception("[BACKEND] request error: %s", endpoint)
        return None
    except Exception:
        logger.exception("[BACKEND] unexpected error: %s", endpoint)
        return None


def post_json_with_retries(
    url: Text,
    payload: dict[Text, Any],
    headers: Optional[dict[Text, Any]] = None,
    retries: int = 3,
    delay: int = 2,
) -> Optional[dict[Text, Any]]:
    """Envía un POST HTTP con JSON. Optimizado nativamente con requests y reintentos."""
    if headers is None:
        headers = {}
        
    headers["Content-Type"] = "application/json"
    
    if HELPDESK_TOKEN and "Authorization" not in headers:
        headers["Authorization"] = f"Bearer {HELPDESK_TOKEN}"

    for attempt in range(retries):
        try:
            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10,
            )
            if resp.ok:
                return resp.json() if resp.text else {}
            
            logger.warning(
                "[WARN] Intento %s/%s devolvió estado no exitoso %s para %s",
                attempt + 1, retries, resp.status_code, url
            )
        except requests.RequestException as e:
            logger.warning(
                "[WARN] Intento %s/%s falló para %s: %s",
                attempt + 1, retries, url, e
            )
            
        time.sleep(delay)
    return None


def _json_payload_from_text(text: Text) -> dict[Text, Any]:
    """Parsea una cadena de texto plana a un diccionario JSON estruturado."""
    try:
        return json.loads(text) if text else {}
    except ValueError:
        return {"text": text}


# ================================================================
# NOTIFICATION SERVICES (SMTP)
# ================================================================

def send_email(subject: str, body: str, to_addr: str) -> bool:
    """Envía correos electrónicos transaccionales usando TLS seguro."""
    server = os.getenv("SMTP_SERVER")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")

    if not (server and user and password and to_addr):
        return False

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to_addr

        port = int(os.getenv("SMTP_PORT", "587"))

        with smtplib.SMTP(server, port, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(user, password)
            smtp.sendmail(user, [to_addr], msg.as_string())

        return True

    except Exception:
        logger.exception("send_email error")
        return False


# ================================================================
# INTERACTION & UI FLOW HELPERS
# ================================================================

def send_login_hint(
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    text: str,
) -> None:
    """Dispara un mensaje de sugerencia de inicio de sesión de manera controlada."""
    dispatcher.utter_message(text=text)
    dispatcher.utter_message(response="utter_login_hint")