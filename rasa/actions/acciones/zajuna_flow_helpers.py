# ruta: rasa/actions/acciones/zajuna_flow_helpers.py
from __future__ import annotations

import logging
from typing import Any, Optional, Dict

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

from ..common import (
    backend_get,
    get_user_context,
    is_authenticated,
)
from ..core.llm_engine import run_llm

logger = logging.getLogger(__name__)

# ================================================================
# CONFIG BASE
# ================================================================

DEFAULT_BASE_URL = "https://zajuna.edu"


# ================================================================
# CONTEXTO
# ================================================================

def get_ctx(tracker: Tracker) -> dict[str, Any]:  # MEJORA: Tipado nativo dict
    return get_user_context(tracker)


def base_url(tracker: Tracker) -> str:
    value = (
        tracker.get_slot("zajuna_base_url")
        or ""
    ).strip()

    return value or DEFAULT_BASE_URL


# ================================================================
# AUTH LAYER
# ================================================================

def require_auth(
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    accion: str,
    seccion: str,
) -> tuple[bool, Dict[str, Any] | None]:
    """
    Evalúa si la sesión está autenticada.

    Retorna:

        (False, None)
            → El usuario ya está autenticado y el flujo puede continuar.

        (True, llm_request)
            → El flujo debe detenerse y la Action llamadora deberá
              enviar la solicitud al ActionHandleWithLLM.
    """

    if is_authenticated(tracker):
        return False, None

    url = base_url(tracker)

    prompt = (
        "Eres un tutor virtual del SENA.\n"
        "Explica al estudiante que necesita iniciar sesión para continuar.\n"
        f"Acción: {accion}\n"
        f"Sección: {seccion}\n"
        "Da instrucciones simples y numeradas."
    )

    fallback = (
        f"🔐 Para {accion} necesitas iniciar sesión en Zajuna.\n"
        f"1. Ingresa a {url}\n"
        "2. Inicia sesión\n"
        f"3. Ve a {seccion}"
    )

    llm_request = {
        "instruction": prompt,
        "context": {
            "flujo": "auth_required",
            "accion": accion,
            "seccion": seccion,
        },
        "fallback": fallback,
    }

    # Mantener la pista visual de autenticación.
    dispatcher.utter_message(
        response="utter_login_hint"
    )

    return True, llm_request

# ================================================================
# BACKEND WRAPPER
# ================================================================

def safe_backend_get(
    tracker: Tracker,
    endpoint: str,
    timeout: int = 10,
    default: Any = None,
) -> Any:
    """
    Encapsula las llamadas GET al backend mitigando caídas o timeouts inesperados.
    """
    try:
        result = backend_get(
            tracker=tracker,
            endpoint=endpoint,
            timeout=timeout,
        )

        return result if result is not None else default

    except Exception:
        # MEJORA: Lazy formatting para evitar formateo explícito de strings en errores recurrentes
        logger.exception("[BACKEND] error endpoint=%s", endpoint)
        return default


# ================================================================
# LLM WRAPPER
# ================================================================

def safe_llm(
    prompt: str,
    tracker: Tracker,
    fallback: str = "",
    context: Optional[dict[str, Any]] = None,  # MEJORA: Tipado nativo dict
) -> str:
    """
    Envoltura de ejecución robusta para inferencia de texto mediante LLM Core.
    """
    try:
        result = run_llm(
            prompt=prompt,
            tracker=tracker,
            context=context or {},
            fallback=fallback,
        )

        return (
            result.strip()
            if result
            else fallback
        )

    except Exception:
        logger.exception("[LLM] safe_llm error de inferencia")
        return fallback


# ================================================================
# FORMATTERS
# ================================================================

def format_list(
    items: list[dict[str, Any]],  # MEJORA: Tipado nativo list[dict]
    fields: list[str],            # MEJORA: Tipado nativo list
    prefix: str = "- ",
) -> str:
    """
    Convierte una colección de diccionarios de datos en strings planos formateados con pipes.
    """
    lines: list[str] = []

    for item in items:
        parts: list[str] = []

        for field in fields:
            value = item.get(field)

            if value is None:
                value = ""

            parts.append(str(value))

        lines.append(prefix + " | ".join(parts))

    return "\n".join(lines)


def format_empty(message: str) -> str:
    """Retorna un string de contingencia para campos vacíos."""
    return message


# ================================================================
# PROMPT BUILDER
# ================================================================

def build_prompt(
    role: str,
    content: str,
    max_paragraphs: int = 3,
) -> str:
    """
    Estructura la base del prompt del sistema para homogeneizar la personalidad del bot.
    """
    return (
        f"Eres {role}.\n\n"
        f"{content}\n\n"
        f"Responde en máximo {max_paragraphs} párrafos "
        "en español neutro."
    )


# ================================================================
# DOMAIN HELPERS
# ================================================================

def get_user_mode(tracker: Tracker) -> str:
    """Obtiene el rol o modo actual del usuario en la sesión."""
    return get_ctx(tracker).get("mode", "invitado")


def get_email(tracker: Tracker) -> Optional[str]:
    """Recupera el correo electrónico del estudiante autenticado."""
    return get_ctx(tracker).get("email")


# ================================================================
# LOG HELP
# ================================================================

def log_context(tracker: Tracker, label: str = "[BOT]") -> None:
    """Registra en logs la metadata segura de la sesión sin comprometer PII."""
    ctx = get_ctx(tracker)

    safe_ctx = {
        "mode": ctx.get("mode"),
    }

    logger.info(
        "%s ctx=%s",
        label,
        safe_ctx,
    )

# ================================================================
# MIGRACIÓN DESDE TOOLS.PY (FUNCIONALIDAD CENTRALIZADA)
# ================================================================

def get_ctx_safe(tracker: Tracker) -> dict[str, Any]:
    """
    Versión consolidada y blindada contra fallos del antiguo 'get_ctx' de tools.py.
    """
    latest_msg = tracker.latest_message or {}
    intent_data = latest_msg.get("intent") or {}
    
    return {
        "user_id": tracker.sender_id,
        "intent": intent_data.get("name", "unknown"),
        "text": latest_msg.get("text", ""),
        "slots": tracker.current_slot_values()
    }

# Nota: La función 'require_auth' ya la tienes definida en este mismo archivo 
# con mucha más potencia (usa LLM y prompts oficiales), por lo que 
# simplemente borraremos la versión débil de 'tools.py'.