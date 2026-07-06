# ruta: rasa/actions/core/llm_engine.py
from __future__ import annotations

import logging
import os
from typing import Any, Optional

import requests
from rasa_sdk import Tracker

from .prompts import build_prompt,PROMPT_SYSTEM 

logger = logging.getLogger(__name__)

# ================================================================
# 🧠 CONFIG LLM (Docker & Ollama Ready)
# ================================================================
LLM_BASE_URL = os.getenv(
    "LLM_URL",
    "http://ollama:11434/api/chat"
)


LLM_TIMEOUT = int(
    os.getenv(
        "LLM_TIMEOUT",
        os.getenv("OLLAMA_TIMEOUT", "120")
    )
)

PRIMARY_MODEL = os.getenv("LLM_MODEL", "tinyllama:latest")
FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "tinyllama:latest")
MAX_TOKENS = int(
    os.getenv(
        "OLLAMA_MAX_TOKENS",
        "100"
    )
)
MAX_PROMPT_CHARS = int(
    os.getenv(
        "LLM_MAX_PROMPT_CHARS",
        "6000",
    )
)
logger.info(
    "[LLM CONFIG] URL=%s MODEL=%s TIMEOUT=%s MAXTOKENS=%s",
    LLM_BASE_URL,
    PRIMARY_MODEL,
    LLM_TIMEOUT,
    MAX_TOKENS,
)

def warm_up_model():
    try:
        logger.info("[LLM] Realizando warm-up de Ollama...")
        requests.post(
            LLM_BASE_URL,
            json={
                "model":"phi3:mini",
                "messages":[
                    {
                        "role":"user",
                        "content":"hola"
                    }
                ],
                "stream":False
            },
            timeout=10,
        )
    except:
        pass

# Ejecuta el warm-up una vez al importar el módulo
warm_up_model()

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
def _call_model(
    model: str,
    prompt: str,
    dispatcher: Any = None,
) -> str:

    try:

        if len(prompt) > MAX_PROMPT_CHARS:

            logger.warning(
                "[LLM] Prompt demasiado largo (%d), recortando a %d chars",
                len(prompt),
                MAX_PROMPT_CHARS,
            )

            prompt = prompt[-MAX_PROMPT_CHARS:]

        clean_prompt = (
            prompt
            .replace("\r\n", "\n")
            .strip()
        )

        logger.info(
            "[OLLAMA] Enviando request al modelo=%s (timeout=%s)",
            model,
            LLM_TIMEOUT,
        )

        logger.debug(
            "[OLLAMA] Prompt enviado:\n%s",
            clean_prompt,
        )

        response = requests.post(
            LLM_BASE_URL,
            json={
                "model": model,

                "messages": [

                    {
                        "role": "system",
                        "content": PROMPT_SYSTEM,
                    },

                    {
                        "role": "user",
                        "content": clean_prompt,
                    },

                ],

                "stream": False,

                "keep_alive": "24h",

                "options": {

                    "num_predict": MAX_TOKENS,

                    "temperature": 0.3,

                    "num_ctx": 2048,

                    "top_k": 10,

                    "repeat_penalty": 1.15,

                    # Puedes dejar los stop o quitarlos.
                    # Yo los dejaría comentados durante las pruebas.

                    # "stop": [
                    #     "USER:",
                    #     "SYSTEM:",
                    #     "ASSISTANT:",
                    # ],

                },
            },
            timeout=LLM_TIMEOUT,
        )

        if response.status_code != 200:

            logger.error(
                "[LLM] Error de Ollama (Detalle): %s",
                response.text,
            )

            response.raise_for_status()

        data = response.json()

        respuesta = (
            data.get("message", {})
                .get("content", "")
                .strip()
        )

        if respuesta.startswith("SYSTEM:"):

            logger.warning(
                "[LLM] El modelo devolvió el prompt."
            )

        elif respuesta.startswith("Eres Tutor"):

            logger.warning(
                "[LLM] TinyLlama comenzó copiando las instrucciones."
            )

        logger.info(
            "[LLM] Respuesta recibida (%d caracteres)",
            len(respuesta),
        )

        logger.debug(
            "[OLLAMA] Respuesta completa:\n%s",
            respuesta,
        )

        return respuesta

    except (
        requests.exceptions.ReadTimeout,
        requests.exceptions.ConnectTimeout,
    ) as e:

        logger.error(
            "[LLM] Timeout de Ollama: %s",
            str(e),
        )

        if dispatcher:

            dispatcher.utter_message(
                text=(
                    "Estoy procesando tu consulta, dame un segundo..."
                    " el sistema está un poco lento hoy."
                    " ¿Podrías intentar enviarme la pregunta de nuevo?"
                )
            )

        return "ERROR_TIMEOUT"

    except Exception as e:

        logger.exception(
            "[LLM] model call failed para %s -> %s",
            model,
            str(e),
        )

        return ""

# ================================================================
# 🚀 MAIN ENGINE (PRODUCTION GRADE)
# ================================================================
def run_llm(
    prompt: str,
    tracker: Optional[Tracker] = None,
    context: Optional[dict[str, Any]] = None,
    fallback: str = "",
    use_system_prompt: bool = True,
    dispatcher: Optional[Any] = None,
) -> str:
    """
    Orquesta la inferencia generativa del Tutor Virtual con optimización de prompts.
    """

    sane_prompt = _sanitize(prompt)
    if not sane_prompt:
        return fallback

    try:
        user_id = getattr(tracker, "sender_id", "anónimo")
        context_data = context or {}
        if context_data:
      
            context_data.pop("requires_auth", None)
            context_data.pop("auth_state", None)
        # =====================================================
        # MEJORA: Prompt dinámico y minimalista
        # Utiliza el flujo conversacional para decidir cuándo
        # enviar un prompt ligero o un prompt completo.
        # =====================================================

        flow = context_data.get(
            "flujo",
            "general",
        )

        es_prompt_simple = (

            len(sane_prompt) < 80

            and flow == "general"

            and not context_data.get("materia")

        )

        if use_system_prompt:

            if es_prompt_simple:

                # ---------------------------------------------
                # PROMPT LIGERO
                # Para saludos, agradecimientos y consultas
                # generales muy cortas.
                # ---------------------------------------------

                final_prompt = (
                    f"{PROMPT_SYSTEM}\n\n"
                    "SYSTEM:\n"
                    "Responde de forma breve y natural.\n\n"
                    "USER:\n"
                    f"{sane_prompt}\n\n"
                    "ASSISTANT:\n"
                )

                logger.info(
                    "[LLM] Ejecutando con PROMPT_SYSTEM LIGERO"
                )

            else:

                # ---------------------------------------------
                # PROMPT COMPLETO
                # Consultas académicas, soporte,
                # autenticación, ayuda o cualquier flujo que
                # requiera contexto adicional.
                # ---------------------------------------------

                final_prompt = build_prompt(
                    base_prompt=sane_prompt,
                    tracker=tracker,
                    context=context_data,
                )

                logger.info(
                    "[LLM] Ejecutando con PROMPT_SYSTEM COMPLETO"
                )

        else:

            final_prompt = sane_prompt

            logger.info(
                "[LLM] Ejecutando SIN PROMPT_SYSTEM"
            )

        logger.info(
            "[LLM] Inferencia. Prompt len=%d",
            len(final_prompt),
        )

        # =====================================================
        # MODELO PRINCIPAL Y FAILOVER
        # =====================================================
        result = _call_model(PRIMARY_MODEL, final_prompt, dispatcher=dispatcher)

        if not result:
            logger.warning("[LLM] Fallo en primario, intentando fallback")
            result = _call_model(FALLBACK_MODEL, final_prompt, dispatcher=dispatcher)

        return result.strip() if result and result != "ERROR_TIMEOUT" else fallback

    except Exception as e:
        logger.exception("[LLM CRITICAL ERROR] %s", str(e))
        return fallback

def run_llm_safe(*args, **kwargs) -> str:
    """
    Envoltura heredada para mantener compatibilidad
    con llamadas legacy.
    """
    return run_llm(*args, **kwargs)