# ruta: rasa/actions/core/llm_engine.py
from __future__ import annotations

import logging
import os
from typing import Any, Optional

import requests
from rasa_sdk import Tracker

from .prompts import build_prompt

logger = logging.getLogger(__name__)

# ================================================================
# 🧠 CONFIG LLM (Docker & Ollama Ready)
# ================================================================
LLM_BASE_URL = os.getenv(
    "LLM_URL",
    "http://ollama:11434/api/generate"
)

# MEJORA: Aumento defensivo del timeout por defecto a 30s para mitigar picos de latencia en frío
LLM_TIMEOUT = int(
    os.getenv(
        "LLM_TIMEOUT",
        os.getenv("OLLAMA_TIMEOUT", "120")
    )
)

PRIMARY_MODEL = os.getenv("LLM_MODEL", "llama3")
FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "phi3:mini")
MAX_TOKENS = int(
    os.getenv(
        "OLLAMA_MAX_TOKENS",
        "160"
    )
)

logger.info(
    "[LLM CONFIG] URL=%s MODEL=%s TIMEOUT=%s",
    LLM_BASE_URL,
    PRIMARY_MODEL,
    LLM_TIMEOUT,
)

# ================================================================
# 🧼 SAFE INPUT
# ================================================================
def _sanitize(text: str) -> str:
    """
    Sanea y trunca el texto de entrada para evitar ataques de inyección 
    de prompts o desbordamiento de ventanas de contexto en Ollama.
    """
    if not text:
        return ""
    return text.strip()[:4000]


# ================================================================
# 🚀 INTERNAL CALL (Ollama API Layer)
# ================================================================
def _call_model(model: str, prompt: str) -> str:
    try:
        response = requests.post(
            LLM_BASE_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": MAX_TOKENS,
                    "temperature": 0.3,
                },
            },
            timeout=LLM_TIMEOUT,
        )

        response.raise_for_status()
        data = response.json()
        return data.get("response", "") or ""

    except Exception as e:
        logger.exception(
            "[LLM] model call failed para %s -> %s",
            model,
            str(e)
        )
        return ""


# ================================================================
# 🚀 MAIN ENGINE (PRODUCTION GRADE)
# ================================================================
def run_llm(
    prompt: str,
    tracker: Optional[Tracker] = None,
    context: Optional[dict[str, Any]] = None,  # MEJORA: Tipo nativo dict
    fallback: str = "",
) -> str:
    """
    Orquesta la inferencia generativa del Tutor Virtual. 
    Construye el prompt del sistema integrado con el contexto de Rasa y aplica failover.
    """
    sane_prompt = _sanitize(prompt)
    if not sane_prompt:
        return fallback

    try:
        user_id = getattr(tracker, "sender_id", "anónimo")
        
        # CORRECCIÓN: Inyección real de contexto de Rasa y prompts del sistema del SENA.
        # Originalmente se ignoraban 'tracker' y 'context', rompiendo la memoria del bot.
        context_data = context or {}
        
        # Llama a tu generador de prompts unificado para estructurar el input final hacia Ollama
        final_prompt = build_prompt(
            base_prompt=sane_prompt,
            tracker=tracker,
            context=context_data
        )
        logger.info(
            "[DEBUG] PROMPT PREVIEW:\n%s",
            final_prompt[:2000]
        )
        logger.info(
            "[LLM] Ejecutando inferencia. Prompt final len=%s para usuario=%s",
            len(final_prompt),
            user_id,
        )

        # Intento de Inferencia con Modelo Principal (Estrategia A)
        result = _call_model(PRIMARY_MODEL, final_prompt)

        # Failover Activo con Modelo Secundario si el principal cae o devuelve vacío (Estrategia B)
        if not result:
            logger.warning("[LLM] Modelo primario (%s) falló o agotó tiempo límite → Conmutando a fallback", PRIMARY_MODEL)
            result = _call_model(FALLBACK_MODEL, final_prompt)

        return result.strip() if result else fallback

    except Exception as e:
        logger.exception(
            "[LLM CRITICAL ERROR] %s",
            str(e)
        )
        return fallback


def run_llm_safe(*args, **kwargs) -> str:
    """Envoltura heredada para mantener la compatibilidad con llamadas legacy."""
    return run_llm(*args, **kwargs)