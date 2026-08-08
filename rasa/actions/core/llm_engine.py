# ruta: rasa/actions/core/llm_engine.py
from __future__ import annotations

import logging
import os
import time
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
        "512"
    )
)
MAX_PROMPT_CHARS = int(
    os.getenv(
        "LLM_MAX_PROMPT_CHARS",
        "5000",
    )
)
logger.info(
    "[LLM CONFIG] URL=%s MODEL=%s TIMEOUT=%s MAXTOKENS=%s",
    LLM_BASE_URL,
    PRIMARY_MODEL,
    LLM_TIMEOUT,
    MAX_TOKENS,
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

def warm_up_model():
    try:
        logger.info("[LLM] Iniciando warm-up de Ollama...")

        response = requests.post(
            LLM_BASE_URL,
            json={
                "model": PRIMARY_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": PROMPT_SYSTEM,
                    },
                    {
                        "role": "user",
                        "content": (
                            "Explica brevemente qué es TCP/IP "
                            "en máximo tres líneas."
                        ),
                    },
                ],
                "stream": False,
                "keep_alive": "24h",
            },
            timeout=90,
        )

        logger.info(
            "[LLM] Warm-up finalizado. status=%s",
            response.status_code,
        )

    except Exception as e:
        logger.warning(
            "[LLM] Warm-up falló: %s",
            e,
        )

# ================================================================
# 🚀 Ejecutar warm-up al iniciar el Action Server
# ================================================================
warm_up_model()


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
                "[LLM] Prompt demasiado largo (%d), recortando a %d caracteres desde el inicio.",
                len(prompt),
                MAX_PROMPT_CHARS,
            )

            prompt = prompt[:MAX_PROMPT_CHARS]

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
            len(clean_prompt),
        )
        
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

                "temperature": 0.0,

                "num_predict": MAX_TOKENS,

                "num_ctx": 4096,

                "top_k": 15,

                "top_p": 0.8,

                "repeat_penalty": 1.20,

            },

        }

        logger.info(
            "[LLM] SYSTEM=%d chars | USER=%d chars | TOTAL=%d chars",
            len(PROMPT_SYSTEM),
            len(clean_prompt),
            len(PROMPT_SYSTEM) + len(clean_prompt),
        )
        inicio_request = time.perf_counter()

        logger.info(
            "[LLM TIMING] Iniciando requests.post()"
        )
        response = requests.post(
            LLM_BASE_URL,
            json=payload,
            timeout=LLM_TIMEOUT,
        )
        fin_request = time.perf_counter()

        logger.info(
            "[LLM TIMING] requests.post() tardó %.2f segundos",
            fin_request - inicio_request,
        )
        response.raise_for_status()

        data = response.json()
       
        logger.info(
            "[OLLAMA DURATIONS] total=%.2f ms | load=%.2f ms | prompt=%.2f ms | eval=%.2f ms",
            data.get("total_duration", 0) / 1_000_000,
            data.get("load_duration", 0) / 1_000_000,
            data.get("prompt_eval_duration", 0) / 1_000_000,
            data.get("eval_duration", 0) / 1_000_000,
        )

        logger.info(
            "[OLLAMA TOKENS] prompt=%s | generated=%s",
            data.get("prompt_eval_count"),
            data.get("eval_count"),
        )

        respuesta = (
            data.get("message", {})
                .get("content", "")
                .strip()
        )

        # ----------------------------------------------------
        # Evitar respuestas vacías
        # ----------------------------------------------------

        if not respuesta.strip():

            logger.warning(
                "[LLM] Respuesta vacía."
            )

            return ""

        
        # ----------------------------------------------------
        # Mostrar respuesta completa para depuración
        # ----------------------------------------------------

        logger.info(
            "[LLM] Respuesta recibida (%d caracteres)",
            len(respuesta),
        )

        logger.debug(
           "[LLM] Respuesta:\n%s",
           respuesta,
        )
        
        
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

        # ----------------------------------------------------
        # Detectar cuando el modelo devuelve el prompt
        # completo en lugar de una respuesta.
        # ----------------------------------------------------

        inicio = respuesta[:500]

        patrones_prompt = (
            "Contexto de la conversación",
            "Consulta del estudiante:",
            "Historial reciente:",
            "Memoria semántica relevante:",
            "Última respuesta generada por el tutor:",
            "Macroflujo:",
            "Subflujo:",
            "Materia:",
            "Rol:",
        )

        coincidencias = sum(
           1 for patron in patrones_prompt
           if patron in inicio
        )

        # Solo consideramos que el modelo devolvió el prompt
        # si aparecen varios indicadores del contexto.
        if coincidencias >= 3:
            logger.warning(
                "[LLM] El modelo parece haber devuelto el prompt "
                "(%d coincidencias detectadas).",
                coincidencias,
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

        flow = (
           context_data.get("macroflujo")
           or context_data.get("flujo")
           or "general"
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

        if result.strip() == sane_prompt.strip():

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
