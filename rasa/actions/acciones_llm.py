# ruta: rasa/actions/acciones_llm.py
from __future__ import annotations

"""
ActionHandleWithLLM

Acción principal encargada de orquestar la interacción entre Rasa,
la memoria semántica y el motor LLM.

Responsabilidades del módulo:

- Detectar el flujo conversacional.
- Recuperar contexto conversacional.
- Recuperar memoria semántica.
- Construir el prompt apropiado.
- Invocar el motor LLM.
- Devolver la respuesta al usuario.

La lógica específica de cada responsabilidad se implementa mediante
métodos privados de la clase ActionHandleWithLLM para mantener el
principio de responsabilidad única (SRP).
"""

import logging
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    EventType,
    FollowupAction,
    SlotSet,
)
from rasa_sdk.types import DomainDict

# ---------------------------------------------------------------------
# Memoria semántica
# ---------------------------------------------------------------------

from .actions_semantic_memory import (
    retrieve_similar,
    store_message,
)

# ---------------------------------------------------------------------
# Motor LLM
# ---------------------------------------------------------------------

from .core.llm_engine import (
    get_last_turns,
    run_llm,
)

# ---------------------------------------------------------------------
# Utilidades NLP
# ---------------------------------------------------------------------

from .core.nlp_utils import (
    anonymize_text,
    detectar_materia,
)

# ---------------------------------------------------------------------
# Prompts base
# ---------------------------------------------------------------------

from .core.prompts import (
    MATERIAS,
    PROMPT_SYSTEM,
    PROMPT_TEMPLATE,
)

# ---------------------------------------------------------------------
# Configuración del módulo
# ---------------------------------------------------------------------

logger = logging.getLogger(__name__)

#: Número máximo de intentos permitidos durante formularios
#: (se mantiene por compatibilidad con el flujo existente).
MAX_INTENTOS_FORM: int = 3


class ActionHandleWithLLM(Action):
    """
    Acción principal encargada de orquestar la interacción entre
    Rasa, la memoria semántica y el motor LLM.

    La clase mantiene la misma interfaz pública para garantizar
    compatibilidad con la arquitectura existente, pero organiza
    internamente la lógica por responsabilidades.
    """

    FLOW_AUTH = "auth"
    FLOW_ACADEMIC = "academic"
    FLOW_HELP = "help"
    FLOW_GENERAL = "general"

    def name(self) -> Text:
        return "action_handle_with_llm"

    # ==========================================================
    # ORQUESTACIÓN DEL PROMPT
    # ==========================================================

    def _build_prompt(
        self,
        tracker: Tracker,
    ) -> str:
        """
        Punto único de construcción del prompt.

        NO contiene lógica de negocio.

        Detecta el flujo y delega al builder correspondiente.
        """

        flow = self._detect_flow(tracker)

        logger.info(
            "[LLM] Flow detectado: %s",
            flow,
        )

        if flow == self.FLOW_AUTH:
            return self._build_auth_prompt(tracker)

        if flow == self.FLOW_ACADEMIC:
            return self._build_academic_prompt(tracker)

        if flow == self.FLOW_HELP:
            return self._build_help_prompt(tracker)

        return self._build_general_prompt(tracker)

    # ==========================================================
    # DETECCIÓN DEL FLUJO
    # ==========================================================

    def _detect_flow(
        self,
        tracker: Tracker,
    ) -> str:
        """
        Determina qué flujo debe ejecutar el LLM.

        El orden de evaluación es importante:

        1. Autenticación
        2. Académico
        3. Ayuda
        4. Conversación general
        """

        if tracker.get_slot("requires_auth"):
            return self.FLOW_AUTH

        latest = tracker.latest_message or {}

        intent = (
            latest.get("intent", {})
            .get("name", "")
        )

        if intent == "aprender_tema":
            return self.FLOW_ACADEMIC

        if intent == "ayuda":
            return self.FLOW_HELP

        return self.FLOW_GENERAL

    # ==========================================================
    # BUILDERS ESPECIALIZADOS
    # ==========================================================

    def _build_auth_prompt(
        self,
        tracker: Tracker,
    ) -> str:
        """
        Prompt especializado para solicitudes que requieren autenticación.
        """

        return """
El usuario intenta acceder a información privada
pero aún no está autenticado.

Debes:

1. Explicar brevemente el motivo.
2. Indicar que por seguridad no puedes mostrar datos personales.
3. Explicar cómo iniciar sesión.
4. No inventar información del estudiante.
"""

    def _build_academic_prompt(
        self,
        tracker: Tracker,
    ) -> str:
        """
        Construye el prompt académico.

        La construcción del contenido pedagógico permanece
        desacoplada del resto de flujos.
        """

        latest = tracker.latest_message or {}

        pregunta = latest.get(
            "text",
            "",
        )

        materia = (
            tracker.get_slot("materia_detectada")
            or detectar_materia(pregunta)
            or "General"
        )

        materia_key = str(
            materia
        ).lower()

        rol = (
            tracker.get_slot("rol_academico")
            or MATERIAS.get(
                materia_key,
                "Tutor Académico General",
            )
        )

        return f"""
ROL PEDAGÓGICO:
{rol}

ASIGNATURA:
{materia}

CONSULTA DEL ESTUDIANTE:
{pregunta}

INSTRUCCIONES

- Explica paso a paso.
- Utiliza ejemplos.
- Adapta el lenguaje a estudiantes.
- Divide los temas complejos.
- Finaliza preguntando si desea profundizar.
"""

    # ==========================================================
    # HELP PROMPT
    # ==========================================================

    def _build_help_prompt(
        self,
        tracker: Tracker,
    ) -> str:
        """
        Construye el prompt para solicitudes de ayuda.

        Este flujo no consulta memoria semántica ya que su objetivo
        es orientar al usuario sobre las capacidades del tutor.
        """

        historial = self._build_history(tracker)

        return f"""
El usuario ha solicitado ayuda.

Actúas como el Tutor Virtual del SENA.

Debes:

1. Explicar qué tipo de consultas puedes responder.
2. Explicar qué información académica requiere autenticación.
3. Invitar al estudiante a realizar una consulta concreta.
4. Mantener un tono cordial y profesional.

Historial reciente:

{historial}
"""

    # ==========================================================
    # GENERAL PROMPT
    # ==========================================================

    def _build_general_prompt(
        self,
        tracker: Tracker,
    ) -> str:
        """
        Construye el prompt para conversación general.

        Este método únicamente coordina la obtención del contexto;
        no implementa directamente la lógica de memoria ni historial.
        """

        latest = tracker.latest_message or {}

        last_user = latest.get(
            "text",
            "",
        )

        intent = (
            latest.get("intent", {})
        )

        intent_name = intent.get(
            "name",
            "desconocido",
        )

        intent_confidence = intent.get(
            "confidence",
            0.0,
        )

        memory = ""

        if last_user: 
            memory =self._recover_semantic_memory(
            tracker=tracker,
            text=last_user,
        )

        historial = self._build_history(
            tracker,
        )

        return f"""
Contexto recuperado:

{memory or "Sin contexto previo relevante."}

Intent detectado:
{intent_name}

Confianza:
{intent_confidence:.3f}

Último mensaje del usuario:

{anonymize_text(last_user)}

Historial reciente:

{historial}

Instrucciones:

- Responde únicamente a la consulta realizada.
- No inventes información.
- Usa el contexto únicamente cuando sea relevante.
- Si el contexto no aporta valor, ignóralo.
- Mantén respuestas claras, útiles y breves.
"""
    # ==========================================================
    # MEMORIA SEMÁNTICA
    # ==========================================================

    def _recover_semantic_memory(
        self,
        tracker: Tracker,
        text: str,
    ) -> str:
        """
        Recupera contexto semántico previamente almacenado.

        Nunca genera excepciones hacia arriba.
        En caso de error simplemente devuelve una cadena vacía.
        """
        session = tracker.get_slot(
            "session_id"
        )
        if not text.strip():
            return ""

        try:

            logger.debug(
                "[LLM] Recuperando memoria semántica..."
            )

            memory = retrieve_similar(
                text=text,
                user_id=tracker.sender_id,
                session_id=tracker.get_slot("session_id"),
            )

            if not memory:
                return ""

            recovered = memory.get(
                "text",
                "",
            ).strip()

            if recovered:

                logger.debug(
                    "[LLM] Memoria recuperada correctamente."
                )

                return (
                    "Contexto previo relevante:\n"
                    f"{recovered}"
                )

        except Exception:

            logger.exception(
                "[LLM] Error recuperando memoria semántica"
            )

        return ""

    # ==========================================================
    # HISTORIAL
    # ==========================================================

    def _build_history(
        self,
        tracker: Tracker,
        max_events: int = 6,
        max_lines: int = 4,
    ) -> str:
        """
        Construye un historial resumido y anonimizado.

        El historial se utiliza únicamente como apoyo para el LLM,
        nunca como memoria permanente.
        """

        history: List[str] = []

        raw_events = tracker.events or []

        for event in raw_events[-max_events:]:

            if not isinstance(event, dict):
                continue

            event_type = event.get("event")

            if event_type == "user":

                text = anonymize_text(
                    event.get(
                        "text",
                        "",
                    )
                )

                if text.strip():

                    history.append(
                        f"Usuario: {text}"
                    )

            elif event_type == "bot":

                text = (
                    event.get(
                        "text",
                        "",
                    )
                    or ""
                ).strip()

                if text:

                    history.append(
                        f"Bot: {text}"
                    )

        history = history[-max_lines:]

        logger.debug(
            "[LLM] Historial construido (%d líneas).",
            len(history),
        )

        return "\n".join(history)

    # ==========================================================
    # CONTEXTO PARA EL LLM
    # ==========================================================

    def _build_llm_context(
        self,
        tracker: Tracker,
        flow: str,
    ) -> Dict[str, Any]:

        latest = tracker.latest_message or {}
        intent = latest.get("intent", {}) or {}

        return {
            "flujo": flow,
            "materia": tracker.get_slot("materia_detectada"),
            "rol": tracker.get_slot("rol_academico"),
            "intent": intent.get("name", "desconocido"),
            "confidence": intent.get("confidence", 0.0),
            "session_id": tracker.get_slot("session_id"),
        }
    # ==========================================================
    # INVOCACIÓN DEL LLM
    # ==========================================================

    def _invoke_llm(
        self,
        tracker: Tracker,
        prompt: str,
        flow: str,
    ) -> str:
        """
        Punto único de comunicación con el motor LLM.

        Centraliza la construcción del prompt final y la invocación
        del motor LLM, manteniendo desacoplada la lógica de negocio
        de la estructura del prompt.
        """

        logger.info(
            "[LLM] Preparando prompt para flujo '%s'",
            flow,
        )

        # ------------------------------------------------------
        # Historial reciente
        # ------------------------------------------------------

        history = get_last_turns(
            tracker,
            n=3,
        )

        # ------------------------------------------------------
        # Pregunta actual
        # ------------------------------------------------------

        latest = tracker.latest_message or {}

        user_message = latest.get(
            "text",
            "",
        )

        # ------------------------------------------------------
        # Memoria semántica
        # ------------------------------------------------------

        memory = ""

        if user_message.strip():

            memory = self._recover_semantic_memory(
                tracker=tracker,
                text=user_message,
            )

        # ------------------------------------------------------
        # Instrucciones específicas del flujo
        # ------------------------------------------------------

        instructions = prompt

        # ------------------------------------------------------
        # Prompt final
        # ------------------------------------------------------

        prompt_final = PROMPT_TEMPLATE.format(
            history=history or "Sin historial reciente.",
            memory=memory or "Sin contexto previo relevante.",
            question=user_message,
            instructions=instructions,
        )

        logger.debug(
            "[LLM] Prompt final construido (%d caracteres)",
            len(prompt_final),
        )

        # ------------------------------------------------------
        # Invocación del modelo
        # ------------------------------------------------------

        return run_llm(
            prompt=prompt_final,
            tracker=tracker,
            context=self._build_llm_context(
                tracker,
                flow,
            ),
            use_system_prompt=(
                flow != self.FLOW_ACADEMIC
            ),
            fallback=(
                "Lo siento, en este momento "
                "no puedo generar una respuesta."
            ),
        )

    # ==========================================================
    # RUN
    # ==========================================================

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        """
        Punto de entrada de Rasa.

        Este método actúa únicamente como orquestador.
        No implementa reglas de negocio.
        """

        logger.debug(
            "[ACTION_HANDLE_WITH_LLM] Inicio"
        )

        try:

            flow = self._detect_flow(
                tracker,
            )

            prompt = self._build_prompt(
                tracker,
            )

            logger.debug(
                "[LLM] Prompt generado (%d caracteres)",
                len(prompt),
            )

            respuesta = self._invoke_llm(
                tracker=tracker,
                prompt=prompt,
                flow=flow,
            )

            dispatcher.utter_message(
                text=respuesta,
            )

            logger.info(
                "[LLM] Respuesta enviada correctamente."
            )

            return []

        except Exception:

            logger.exception(
                "[ACTION_HANDLE_WITH_LLM] Error inesperado"
            )

            dispatcher.utter_message(
                text=(
                    "Ocurrió un problema al procesar "
                    "tu solicitud."
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

        logger.debug(
            "[MEMORY_WRAPPER] Persistiendo conversación"
        )

        try:

            latest = tracker.latest_message or {}

            text = latest.get(
                "text",
                "",
            )

            if not text.strip():
                return []

            store_message(
                text=text,
                user_id=tracker.sender_id,
                session_id=(
                    tracker.get_slot("session_id")
                    or tracker.sender_id
                ),
                metadata={
                    "intent": (
                        latest.get("intent", {})
                        .get("name")
                    ),
                    "confidence": (
                        latest.get("intent", {})
                        .get("confidence", 0.0)
                    ),
                },
            )

        except Exception:

            logger.exception(
                "[MEMORY_WRAPPER]"
            )

        return []