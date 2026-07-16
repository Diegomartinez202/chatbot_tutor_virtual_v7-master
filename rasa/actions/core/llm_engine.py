# ruta: rasa/actions/core/llm_engine.py
from __future__ import annotations

import logging
import os
from typing import Any, Optional

import requests
from rasa_sdk import Tracker

from .prompts import PROMPT_SYSTEM 

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

PRIMARY_MODEL = os.getenv("LLM_MODEL", "qwen2.5:3b")
FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "qwen2.5:3b")
MAX_TOKENS = int(
    os.getenv(
        "OLLAMA_MAX_TOKENS",
        "180"
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
                "model": PRIMARY_MODEL,
                "messages":[
                    {
                        "role":"user",
                        "content":"hola"
                    }
                ],
                "stream":False
            },
            timeout=90,
        )
    except:
        pass


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
    logger.warning(">>> ENTRANDO A _call_model")
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
            "[OLLAMA] Enviando request al modelo=%s",
            model,
        )

        logger.debug(
            "[OLLAMA] Prompt enviado:\n%s",
            clean_prompt,
        )

        logger.info("[PROMPT SIZE] %s", len(clean_prompt))
        logger.info("[SYSTEM SIZE] %s", len(PROMPT_SYSTEM))
        
        payload = {

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

                "temperature": 0.2,

                "num_predict": MAX_TOKENS,

                "num_ctx": 2048,

                "top_k": 20,

                "top_p": 0.9,

                "repeat_penalty": 1.20,

            },

        }

        logger.info("=" * 80)
        logger.info("[OLLAMA PAYLOAD]")
        
        logger.info("=" * 80)
        
        
        response = requests.post(
            LLM_BASE_URL,
            json=payload,
            timeout=LLM_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()
       
        respuesta = (
            data.get("message", {})
                .get("content", "")
                .strip()
        )

        # ----------------------------------------------------
        # Evitar respuestas vacías
        # ----------------------------------------------------

        if not respuesta:

            logger.warning(
                "[LLM] Respuesta vacía."
            )

            return ""

        
        # ----------------------------------------------------
        # Mostrar respuesta completa para depuración
        # ----------------------------------------------------

        logger.warning("=" * 80)
        logger.warning("RESPUESTA COMPLETA:")
        logger.warning(respuesta)
        logger.warning("=" * 80)
        
        
        # ----------------------------------------------------
        # Detectar copia del prompt
        # ----------------------------------------------------

        inicio = respuesta[:500]

        patrones_prompt = (
            "Contexto de la conversación",
            "Consulta del estudiante:",
            "Historial reciente:",
            "Memoria relevante:",
            "Flujo:",
            "Materia:",
            "Rol:"
        )

        if any(p in inicio for p in patrones_prompt):
            logger.warning(
                "[LLM] El modelo devolvió el prompt completo."
            )
            return ""

        logger.info(
            "[LLM] Respuesta recibida (%d caracteres)",
            len(respuesta),
        )

        logger.debug(
            "[OLLAMA] Respuesta:\n%s",
            respuesta,
        )
        logger.warning("<<< SALIENDO DE _call_model")
        return respuesta

    except (
        requests.exceptions.ReadTimeout,
        requests.exceptions.ConnectTimeout,
    ) as e:

        logger.error(
            "[LLM] Timeout: %s",
            str(e),
        )

        return "ERROR_TIMEOUT"

    except Exception as e:

        logger.exception(
            "[LLM] Error llamando al modelo: %s",
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
    Orquesta la inferencia del LLM.

    IMPORTANTE

    ActionHandleWithLLM ya entrega un prompt completamente construido
    mediante build_prompt().

    Por lo tanto esta función NO vuelve a construir prompts.
    Su única responsabilidad es:

    - Sanitizar.
    - Limpiar contexto.
    - Invocar Ollama.
    - Gestionar failover.
    - Devolver la respuesta.
    """

    sane_prompt = _sanitize(prompt)

    if not sane_prompt:
        logger.warning("[LLM] Prompt vacío.")
        return fallback

    try:

        context_data = dict(context or {})

        # --------------------------------------------------------
        # Limpiar información interna que nunca debe viajar al LLM
        # --------------------------------------------------------

        context_data.pop("requires_auth", None)
        context_data.pop("auth_state", None)

        flow = context_data.get(
            "flujo",
            "general",
        )

        logger.info(
            "[LLM] Ejecutando flujo '%s'",
            flow,
        )

        logger.info(
            "[LLM] Prompt listo (%d caracteres)",
            len(sane_prompt),
        )

        logger.debug(
            "[LLM] Prompt enviado:\n%s",
            sane_prompt,
        )

        # ========================================================
        # MODELO PRINCIPAL
        # ========================================================

        result = _call_model(
            PRIMARY_MODEL,
            sane_prompt,
            dispatcher=dispatcher,
        )

        # ========================================================
        # FAILOVER
        # ========================================================

        if (
            not result
            and FALLBACK_MODEL != PRIMARY_MODEL
        ):

            logger.warning(
                "[LLM] Intentando modelo fallback..."
            )

            result = _call_model(
                FALLBACK_MODEL,
                sane_prompt,
                dispatcher=dispatcher,
            )

        # ========================================================
        # TIMEOUT
        # ========================================================

        if result == "ERROR_TIMEOUT":

            logger.warning(
                "[LLM] Timeout del modelo."
            )

            return fallback

        # ========================================================
        # RESPUESTA VACÍA
        # ========================================================

        if not result:

            logger.warning(
                "[LLM] El modelo respondió vacío."
            )

            return fallback

        result = result.strip()

        # ========================================================
        # EVITAR QUE EL MODELO DEVUELVA EL PROMPT
        # ========================================================

        if result == sane_prompt:

            logger.warning(
                "[LLM] El modelo devolvió exactamente el prompt recibido."
            )

            return fallback

        if len(result) > 50 and sane_prompt[:50] in result:

            logger.warning(
                "[LLM] El modelo comenzó copiando el prompt."
            )

            return fallback

        logger.info(
            "[LLM] Respuesta generada (%d caracteres)",
            len(result),
        )

        logger.debug(
            "[LLM] Respuesta:\n%s",
            result,
        )

        return result

    except Exception as e:

        logger.exception(
            "[LLM CRITICAL ERROR] %s",
            str(e),
        )

        return fallback


def run_llm_safe(*args, **kwargs) -> str:
    """
    Compatibilidad con llamadas legacy.
    """
    return run_llm(*args, **kwargs)