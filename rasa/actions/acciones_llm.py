# ruta: rasa/actions/acciones_llm.py
from __future__ import annotations

import logging
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import (
    SlotSet,
    EventType,
    FollowupAction,
) 

from .actions_semantic_memory import (
    retrieve_similar,
    store_message,
)
from .core.llm_engine import run_llm, get_last_turns
from .core.nlp_utils import anonymize_text, detectar_materia
from .core.prompts import PROMPT_SYSTEM, MATERIAS

logger = logging.getLogger(__name__)

MAX_INTENTOS_FORM = 3


class ActionHandleWithLLM(Action):

    logger.info(
    "[ACTION_HANDLE_WITH_LLM] INICIO"
    )
    
    def name(self) -> Text:
        return "action_handle_with_llm"

    def _build_prompt(
        self,
        tracker: Tracker,
    ) -> str:

        requires_auth = tracker.get_slot(
            "requires_auth"
        )

        if requires_auth:

            return """
            El usuario intenta acceder a información privada
            pero no está autenticado.

            Tu respuesta debe ser:

            1. Explicar brevemente que por seguridad no puedes mostrar datos personales sin login.
            2. Dar los pasos exactos para autenticarse en:
               https://tu-plataforma.com/login
            3. No inventes datos del estudiante.
            """

        latest = tracker.latest_message or {}

        last_user = latest.get(
            "text",
            ""
        ) or ""

        intent_name = (
            latest.get("intent", {})
            .get("name", "")
        )

        # =====================================================
        # FLUJO ACADÉMICO
        # =====================================================

        if intent_name == "aprender_tema":

            materia = (
                tracker.get_slot(
                    "materia_detectada"
                )
                or detectar_materia(
                    last_user
                )
            )

            materia_key = (
                str(materia).lower()
                if materia
                else "general"
            )

            rol = (
                tracker.get_slot(
                    "rol_academico"
                )
                or MATERIAS.get(
                    materia_key,
                    "Tutor Académico General",
                )
            )

            return self._build_academic_prompt(
                pregunta=last_user,
                materia=str(
                    materia or "General"
                ),
                rol=rol,
            )

        return self._build_generic_prompt(
            tracker
        )

    def _build_academic_prompt(
        self,
        pregunta: str,
        materia: str,
        rol: str,
    ) -> str:

        return f"""
ROL PEDAGÓGICO:
{rol}

ASIGNATURA:
{materia}

CONSULTA DEL ESTUDIANTE:
{pregunta}

INSTRUCCIONES:

- Explica paso a paso.
- Usa ejemplos prácticos.
- Adapta el lenguaje a estudiantes.
- Si el tema es complejo, divídelo en partes.
- Finaliza preguntando si desea profundizar.
"""

    def _build_generic_prompt(
        self,
        tracker: Tracker,
    ) -> str:

        latest = tracker.latest_message or {}

        last_user = latest.get(
            "text",
            ""
        ) or ""

        intent_data = (
            latest.get("intent")
            or {}
        )

        intent_name = intent_data.get(
            "name",
            "desconocido",
        )

        intent_conf = intent_data.get(
            "confidence",
            0.0,
        )

        # =====================================================
        # AYUDA
        # =====================================================

        if intent_name == "ayuda":

            historial = (
                self._get_formatted_history(
                    tracker
                )
            )

            return f"""
El usuario ha solicitado ayuda.

Como tutor virtual:

1. Explica qué tipo de consultas académicas puedes resolver.
2. Explica cómo puede consultar su estado académico si está autenticado.
3. Invítalo a realizar una pregunta específica sobre cualquier tema.

Historial reciente:

{historial}
"""

        # =====================================================
        # MEMORIA SEMÁNTICA
        # =====================================================

        contexto_memoria = ""

        prev = None

        if last_user:

            prev = retrieve_similar(
                text=last_user,
                user_id=tracker.sender_id,
                session_id=tracker.get_slot(
                    "session_id"
                ),
            )

        if prev:

            contexto_memoria = (
                "\n\nContexto previo relevante:\n"
                f"{prev.get('text', '')}"
            )

        # =====================================================
        # HISTORIAL REDUCIDO
        # =====================================================

        history = []

        raw_events = (
            tracker.events
            or []
        )

        for event in raw_events[-6:]:

            if not isinstance(
                event,
                dict,
            ):
                continue

            event_type = event.get(
                "event"
            )

            if event_type == "user":

                text = event.get(
                    "text",
                    ""
                )

                history.append(
                    f"Usuario: {anonymize_text(text)}"
                )

            elif event_type == "bot":

                text = event.get(
                    "text",
                    ""
                )

                if text:

                    history.append(
                        f"Bot: {text}"
                    )

        historial = "\n".join(
            history[-4:]
        )

        return (
            contexto_memoria
            + "\n\n"
            + f"Intent detectado: {intent_name}\n"
            + f"Confianza: {intent_conf}\n\n"
            + f"Último mensaje:\n{anonymize_text(last_user)}\n\n"
            + f"Historial:\n{historial}\n\n"
            + "Responde de forma útil, clara y breve."
        )

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        try:

            prompt = self._build_prompt(
                tracker
            )

            logger.info(
                "[DEBUG] prompt len=%s",
                len(prompt),
            )

            latest = (
                tracker.latest_message
                or {}
            )
            logger.info(
                "[DEBUG] tema_consulta=%s",
                tracker.get_slot("tema_consulta"),
            )

            logger.info(
                "[DEBUG] last_message=%s",
                (
                    tracker.latest_message
                    or {}
                ).get(
                    "text"
                )
            )

            is_academic = (
                latest.get(
                    "intent",
                    {},
                ).get("name")
                == "aprender_tema"
            )

            historial_limpio = get_last_turns(tracker, n=2)
            pregunta_usuario = tracker.latest_message.get("text", "")
            prompt_filtrado = f"{historial_limpio}\nUsuario: {pregunta_usuario}\n\nContexto: {prompt}"
            
            respuesta = run_llm(
                prompt=prompt_filtrado,
                tracker=tracker,
                context={
                    "flujo": (
                        "academico"
                        if is_academic
                        else "action_handle_with_llm"
                    ),
                    "materia": tracker.get_slot(
                        "materia_detectada"
                    ),
                    "rol": tracker.get_slot(
                        "rol_academico"
                    ),
                },
                use_system_prompt=(
                    not is_academic
                ),
                fallback=(
                    "Lo siento, en este momento "
                    "no puedo generar una respuesta."
                ),
            )

            dispatcher.utter_message(
                text=respuesta
            )

            return []

        except Exception:

            logger.exception(
                "[ACTION_HANDLE_WITH_LLM]"
            )

            dispatcher.utter_message(
                text=(
                    "Ocurrió un problema al "
                    "procesar tu solicitud."
                )
            )

            return [
                SlotSet(
                    "requires_auth",
                    None,
                )
            ]

class ActionMemoryWrapper(Action):

    def name(self) -> Text:
        return "action_memory_wrapper"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        logger.info(
        "[MEMORY_WRAPPER] INICIO"
        )
        try:
            latest_msg = tracker.latest_message or {}
            user_msg = latest_msg.get("text", "")

            if user_msg:
                
                prev = retrieve_similar(
                    text=user_msg,
                    user_id=tracker.sender_id
                )

                contexto_memoria = ""

                if prev:
                    logger.info(
                        "[MEMORIA] Contexto recuperado"
                    )

                    contexto_memoria = (
                        "\n\nContexto previo relevante:\n"
                        f"{prev.get('text','')}"
                )


                store_message(
                    text=user_msg,
                    user_id=tracker.sender_id,
                    session_id=(
                        tracker.get_slot("session_id")
                        or tracker.sender_id
                    ),
                    metadata={
                        "intent": tracker.latest_message
                            .get("intent", {})
                            .get("name"),

                        "confidence": tracker.latest_message
                            .get("intent", {})
                            .get("confidence", 0.0)
    }
)

        except Exception as e:
            logger.warning(
                f"[MEMORY_WRAPPER] {e}"
            )

        return []