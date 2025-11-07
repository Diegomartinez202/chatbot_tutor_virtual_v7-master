# rasa/actions/common.py
from __future__ import annotations

import os
import re
import time
import json
import smtplib
import logging
from typing import Any, Dict, Optional
import requests
from email.mime.text import MIMEText
from rasa_sdk import Tracker

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

SMTP_SERVER = (os.getenv("SMTP_SERVER") or "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
SMTP_USER = (os.getenv("SMTP_USER") or "").strip()
SMTP_PASS = (os.getenv("SMTP_PASS") or "").strip()
EMAIL_FROM = (os.getenv("EMAIL_FROM") or SMTP_USER or "bot@ejemplo.com").strip()

REQUEST_TIMEOUT_SECS = int(os.getenv("ACTIONS_HTTP_TIMEOUT", "10"))
MAX_RETRIES = int(os.getenv("ACTIONS_HTTP_RETRIES", "2"))

ACTIONS_PING_HELPDESK = (os.getenv("ACTIONS_PING_HELPDESK") or "false").lower() == "true"

RESET_URL_BASE = (os.getenv("RESET_URL_BASE") or "https://zajuna.edu").rstrip("/")

JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")

# =========================
#   Utilidades HTTP/SMTP
# =========================
def send_email(subject: str, body: str, to_addr: str) -> bool:
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
    try:
        ents = (tracker.latest_message or {}).get("entities") or []
        for ent in ents:
            if (ent.get("entity") == name) and ("value" in ent):
                return str(ent.get("value") or "").strip()
    except Exception:
        pass
    return None

def _json_payload_from_text(text: str) -> Dict[str, Any]:
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

def _is_auth(tracker: Tracker) -> bool:
    return bool(tracker.get_slot("is_authenticated"))

def _backend_base() -> str:
    return (os.getenv("BACKEND_URL") or "").rstrip("/")

def _auth_headers(tracker: Tracker) -> Dict[str, str]:
    token = tracker.get_slot("auth_token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def _has_auth(tracker: Tracker) -> bool:
    meta = (tracker.latest_message or {}).get("metadata") or {}
    auth = meta.get("auth") if isinstance(meta, dict) else {}
    if isinstance(auth, dict) and auth.get("hasToken"):
        return True
    if isinstance(auth, dict) and auth.get("claims"):
        return True
    return False
