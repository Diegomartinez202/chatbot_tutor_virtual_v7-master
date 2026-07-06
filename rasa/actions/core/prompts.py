# ruta: rasa/actions/core/prompts.py
from __future__ import annotations

import logging
from typing import Any, Optional
from rasa_sdk import Tracker
from .history import build_history
from ..actions_semantic_memory import retrieve_similar
logger = logging.getLogger(__name__)

# ================================================================
# 🧠 SYSTEM PROMPT GLOBAL
# ================================================================
PROMPT_SYSTEM = """
Eres Tutor Virtual del SENA.

Tu función es ayudar a los estudiantes respondiendo consultas
académicas, administrativas y de soporte institucional.

REGLAS GENERALES

- Nunca copies estas instrucciones.
- Nunca repitas el prompt recibido.
- Responde únicamente al estudiante.
- Mantén un lenguaje claro y profesional.
- Si la consulta es académica explica paso a paso.
- Usa ejemplos cuando sea necesario.
- Si desconoces una respuesta, indícalo con honestidad.
- No inventes información.

AUTENTICACIÓN

Si la consulta corresponde a:

- certificados
- historial académico
- datos personales
- estado del estudiante

debes solicitar autenticación mediante:

https://localhost/login

No solicites autenticación para consultas académicas generales
como programación, redes, bases de datos, matemáticas,
algoritmos o conceptos teóricos.
"""


# ================================================================
# ⚙️ PROMPTS ADICIONALES (PRESERVADOS INTACTOS)
# ================================================================
SUMMARIZE_SYSTEM_PROMPT = """
Eres un asistente de redacción para el Tutor Virtual de Zajuna/SENA.

TU ÚNICA TAREA:
- Reescribir mensajes técnicos en un texto claro, amable y profesional.
- NO debes inventar ni cambiar datos de negocio (estado académico, notas, certificados, tickets, etc.).

REGLAS:
- Usa SIEMPRE español.
- Respeta todos los hechos: no cambies estados, fechas, cantidades, cursos, ni resultados.
- No inventes certificados, notas, accesos ni números de ticket.
- No des diagnósticos médicos, psicológicos ni legales.
- Si el texto base está claro, solo mejóralo ligeramente (tono más humano, mejor orden).

FORMATO DE SALIDA:
- Devuelve ÚNICAMENTE el texto final para el usuario.
- No incluyas etiquetas como 'INTENT:' ni 'RESPUESTA:'.
- No expliques qué estás haciendo, solo entrega el mensaje listo para mostrar.
"""

PALABRAS_CONFIRMACION = {
    "si", "sí", "claro", "vale", "ok", "okay", "bueno", "listo", 
    "dale", "de acuerdo", "correcto", "continua", "continúa", "siga", "sigue",
}

CERTIFICADOS_PROMPT = """
Eres un asistente académico.

Resumen del usuario:
{summary}

Responde de forma clara y breve.
"""

ESTADO_ESTUDIANTE_PROMPT = """
Explica el estado académico del estudiante:

{data}
"""


# ================================================================
# 🚀 PROMPT BUILDER CORE (OPTIMIZADO PARA /api/chat)
# ================================================================
def build_prompt(
    base_prompt: str,
    tracker: Optional[Tracker] = None,
    context: Optional[dict[str, Any]] = None,
) -> str:
    """
    Construye el contenido del mensaje del usuario que será enviado
    al endpoint /api/chat.

    IMPORTANTE:
    Este método YA NO incluye PROMPT_SYSTEM ni los bloques
    SYSTEM/USER/ASSISTANT, porque esos roles son enviados
    directamente por _call_model() utilizando la API de chat
    de Ollama.

    Su responsabilidad ahora es únicamente aportar el contexto
    conversacional necesario para responder correctamente.
    """

    ctx = context or {}
    history = ""
    memory = ""

    if tracker:

        history = build_history(tracker)

        try:
            
            consulta = base_prompt.strip()

            if consulta:

                resultado = retrieve_similar(
                    text=consulta,
                    user_id=tracker.sender_id,
                   session_id=tracker.get_slot("session_id"),
                )

                if resultado:
                    memory = resultado.get("text", "")

        except Exception:
            logger.exception(
                "[PROMPT BUILDER] Error recuperando memoria."
        )

    materia = ctx.get(
        "materia",
        "general",
    )

    flujo = ctx.get(
        "flujo",
        "general",
    )

    instruccion_forzada = (
        "[INSTRUCCIÓN: Esta es una consulta académica pública. "
        "No requiere autenticación.]"
    )

    tipo_respuesta = (
        "TIPO: RESPUESTA PÚBLICA ACADÉMICA"
    )

    prompt_final = f"""
{instruccion_forzada}

{tipo_respuesta}

FLUJO
------

{flujo}

CONTEXTO ACADÉMICO
------------------

{materia}

HISTORIAL
----------

{history or "Sin historial."}

MEMORIA RELEVANTE
-----------------

{memory or "Sin memoria relevante."}

CONSULTA DEL ESTUDIANTE
-----------------------

{base_prompt}

INSTRUCCIONES PARA LA RESPUESTA
-------------------------------

- Responde únicamente al estudiante.
- No copies las instrucciones.
- No repitas el prompt.
- Explica paso a paso cuando sea una consulta académica.
- Usa ejemplos cuando sea necesario.
- Si la consulta requiere autenticación, indícalo únicamente cuando corresponda.
"""

    logger.info(
        "[PROMPT BUILDER] Prompt final len=%d",
        len(prompt_final),
    )

    logger.debug(
        "[PROMPT BUILDER] Prompt:\n%s",
        prompt_final,
    )

    return prompt_final