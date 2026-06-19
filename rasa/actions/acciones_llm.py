# ruta: rasa/actions/acciones_llm.py
from __future__ import annotations

import logging
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, EventType

from .actions_semantic_memory import (
    retrieve_similar,
    store_message,
)
from .core.llm_engine import run_llm
from .core.nlp_utils import anonymize_text, detectar_materia
from .core.prompts import PROMPT_SYSTEM, MATERIAS

logger = logging.getLogger(__name__)

MAX_INTENTOS_FORM = 3


class ActionHandleWithLLM(Action):

    def name(self) -> Text:
        return "action_handle_with_llm"

    def _build_prompt(
        self,
        tracker: Tracker,
    ) -> str:

        latest = tracker.latest_message or {}
        last_user = latest.get("text", "") or ""
        intent_name = latest.get("intent", {}).get("name", "")

        if intent_name == "aprender_tema":

            materia = (
                tracker.get_slot("materia_detectada")
                or detectar_materia(last_user)
            )

            # MEJORA: Evitar fallos de inicialización si materia viene vacía o nula
            materia_key = str(materia).lower() if materia else "general"

            rol = (
                tracker.get_slot("rol_academico")
                or MATERIAS.get(
                    materia_key,
                    "Tutor Académico General"
                )
            )

            return self._build_academic_prompt(
                pregunta=last_user,
                materia=str(materia or "General"),
                rol=rol,
            )

        return self._build_generic_prompt(tracker)

    def _build_generic_prompt(
        self,
        tracker: Tracker,
    ) -> str:

        latest = tracker.latest_message or {}
        last_user = latest.get("text", "") or ""

        contexto_memoria = ""

        prev = None

        if last_user:
            prev = retrieve_similar(last_user)

        if prev:
            contexto_memoria = (
                "\n\nContexto previo relevante:\n"
                f"{prev.get('text','')}"
            )


        intent_data = latest.get("intent") or {}
        intent_name = intent_data.get("name", "desconocido")
        intent_conf = intent_data.get("confidence", 0.0)

        history = []
        raw_events = tracker.events or []

        # MEJORA: Validación segura del esquema de eventos para prevenir fallos por objetos no mutables
        for event in raw_events[-12:]:
            if not isinstance(event, dict):
                continue

            event_type = event.get("event")

            if event_type == "user":
                text = event.get("text", "")
                history.append(f"Usuario: {anonymize_text(text)}")

            elif event_type == "bot":
                text = event.get("text", "")
                if text:
                    history.append(f"Bot: {text}")

        historial = "\n".join(history[-8:])

        return (
            PROMPT_SYSTEM
            + contexto_memoria
            + "\n\n"
            + f"Intent detectado: {intent_name}\n"
            + f"Confianza: {intent_conf}\n\n"
            + f"Último mensaje:\n{anonymize_text(last_user)}\n\n"
            + f"Historial:\n{historial}\n\n"
            + "Responde de forma útil, clara y breve."
        )

    def _build_academic_prompt(
        self,
        pregunta: str,
        materia: str,
        rol: str,
    ) -> str:

        return f"""
{PROMPT_SYSTEM}

ROL ACADÉMICO:
{rol}

MATERIA DETECTADA:
{materia}

TEMA:
{pregunta}

INSTRUCCIONES OBLIGATORIAS:

1. Explica qué es.
2. Explica conceptos clave.
3. Explica paso a paso.
4. Da ejemplos prácticos.
5. Relaciónalo con formación SENA.
6. Menciona errores comunes.
7. Formula una pregunta de repaso.

Usa lenguaje claro y educativo.
"""

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Unificación a DomainDict para consistencia tipada
    ) -> List[EventType]:

        try:
            prompt = self._build_prompt(tracker)

            respuesta = run_llm(
                prompt=prompt,
                tracker=tracker,
                context={
                    "flujo": "action_handle_with_llm",
                },
                fallback=(
                    "Lo siento, en este momento "
                    "no puedo generar una respuesta."
                ),
            )

            dispatcher.utter_message(text=respuesta)
            return []

        except Exception:
            logger.exception("[ACTION_HANDLE_WITH_LLM]")
            dispatcher.utter_message(
                text="Ocurrió un problema al procesar tu solicitud."
            )
            return []


class ActionMemoryWrapper(Action):

    def name(self) -> Text:
        return "action_memory_wrapper"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Firma estandarizada del SDK
    ) -> List[EventType]:

        try:
            latest_msg = tracker.latest_message or {}
            user_msg = latest_msg.get("text", "")

            if user_msg:
                
                prev = retrieve_similar(user_msg)

                contexto_memoria = ""

                if prev:
                    logger.info(
                        "[MEMORIA] Contexto recuperado"
                    )

                    contexto_memoria = (
                        "\n\nContexto previo relevante:\n"
                        f"{prev.get('text','')}"
                )


                store_message(user_msg)

        except Exception as e:
            logger.warning(
                f"[MEMORY_WRAPPER] {e}"
            )

        return []