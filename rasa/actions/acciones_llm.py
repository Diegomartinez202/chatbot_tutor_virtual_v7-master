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
import time
import logging
from typing import Any, Dict, List, Text
from rasa_sdk.events import ActiveLoop
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

    def _detect_flow(self, tracker: Tracker) -> str:
        # 1. Definimos si es un flujo académico ANTES de mirar la autenticación
        es_academico = (
            tracker.get_slot("tema_consulta") 
            or tracker.get_slot("materia_detectada")
        )

        # 2. Si es académico, retornamos FLOW_ACADEMIC ignorando la autenticación
        if es_academico:
            return self.FLOW_ACADEMIC

        # 3. Solo si NO es académico, verificamos la autenticación
        if tracker.get_slot("requires_auth"):
            return self.FLOW_AUTH

        # ... resto del método (ayuda, general)
        latest = tracker.latest_message or {}
        intent = latest.get("intent", {}).get("name", "")
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
        Prompt especializado para consultas protegidas.
        """

        accion = (
            tracker.get_slot("pending_action")
            or "consultar información personal"
        )

        return f"""
        El usuario intentó realizar la siguiente acción protegida:

    {accion}

    Debes responder como Tutor Virtual del SENA.

    Explica de manera cordial que esa información contiene datos
    personales del estudiante y requiere autenticación.

    Indica claramente:

    1. Que la información está protegida por motivos de privacidad.

    2. Que el chatbot podrá consultar la información una vez el usuario
    inicie sesión.

    3. Que debe ingresar al portal institucional:

    https://localhost/login

    4. Explica los pasos:

    • Abrir el portal.
    • Iniciar sesión con sus credenciales.
    • Regresar al chat.
    • Repetir la consulta.

    No inventes información académica.

    No respondas como si el usuario ya estuviera autenticado.

    No expliques programación ni conceptos académicos.

    Tu único objetivo es ayudar al usuario a autenticarse.
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

        pregunta = (
           tracker.get_slot("tema_consulta")
           or tracker.latest_message.get("text","")
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
    def _build_history(
        self,
        tracker: Tracker,
        max_events: int = 2,
        max_lines: int = 2,
    ) -> str:
        history: List[str] = []
        raw_events = tracker.events or []

        for event in raw_events[-max_events:]:
            if not isinstance(event, dict):
                continue

            event_type = event.get("event")

            if event_type == "user":
                text = anonymize_text(event.get("text", ""))
                # --- MEJORA: Filtro de comandos ---
                if text and not text.startswith("/"): 
                    history.append(f"Usuario: {text}")

            elif event_type == "bot":
                text = (event.get("text", "") or "").strip()
                if text:
                    history.append(f"Bot: {text}")

        history = history[-max_lines:]
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

    def _invoke_llm(self, tracker: Tracker, prompt: str, flow: str) -> str:
        logger.info("[LLM] Preparando prompt para flujo '%s'", flow)

        # Historial (con el filtro aplicado arriba)
        history = "" if flow == self.FLOW_ACADEMIC else self._build_history(tracker)

        # Pregunta actual
        latest = tracker.latest_message or {}
        user_message = (tracker.get_slot("tema_consulta") or latest.get("text", "")) if flow == self.FLOW_ACADEMIC else latest.get("text", "")

        # Memoria semántica
        memory = ""
        if flow != self.FLOW_ACADEMIC and user_message.strip():
            memory = self._recover_semantic_memory(tracker=tracker, text=user_message)

        # Prompt final
        if flow == self.FLOW_ACADEMIC:
            prompt_final = prompt
        else:
            prompt_final = PROMPT_TEMPLATE.format(
                history=history or "Sin historial reciente.",
                memory=memory or "Sin contexto previo relevante.",
                question=user_message,
                instructions=prompt,
            )

        # --- INVOCACIÓN ---
        return run_llm(
            prompt=prompt_final,
            tracker=tracker,
            context=self._build_llm_context(tracker, flow),
            use_system_prompt=(flow != self.FLOW_ACADEMIC), # <--- AQUÍ SE DESACTIVA PARA ACADÉMICO
            fallback="Lo siento, en este momento no puedo generar una respuesta.",
        )

    def run(self, dispatcher, tracker, domain) -> List[EventType]:
        limpieza = [ActiveLoop(None), SlotSet("requested_slot", None)]
        flow = self._detect_flow(tracker)
        
        # 1. Detectar intención
        intent = tracker.get_intent_of_latest_message()
        
        # 2. Si el usuario inicia un tema nuevo, guardamos el tema en el slot
        if intent == "explicacion_academica":
            # Extraemos el tema de la entidad o del mensaje
            nuevo_tema = tracker.latest_message.get("text")
            return limpieza + [SlotSet("tema_actual", nuevo_tema)] + self._ejecutar_procesamiento_llm(dispatcher, tracker, self.FLOW_ACADEMIC)

        # 3. Si el usuario presiona "Continuar tema"
        if intent == "continuar_tema":
            tema_persistido = tracker.get_slot("tema_actual") or "el tema anterior"
            prompt_enriquecido = f"Contexto: {tema_persistido}. Continúa con el siguiente paso lógico. NO saludes, no repitas la introducción, ve directo al grano."
            return self._ejecutar_procesamiento_llm(dispatcher, tracker, flow, prompt=prompt_enriquecido)

        return limpieza + self._ejecutar_procesamiento_llm(dispatcher, tracker, flow)
    def _ejecutar_procesamiento_llm(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, flow: str
    ) -> List[EventType]:
        """
        Método auxiliar que contiene toda tu lógica original de procesamiento.
        """
        try:
            prompt = self._build_prompt(tracker)
            
            logger.debug("[LLM] Prompt generado (%d caracteres)", len(prompt))

            respuesta = self._invoke_llm(
                tracker=tracker,
                prompt=prompt,
                flow=flow,
            )

            # ==========================================================
            # INTERPRETAR RESPUESTA DEL LLM
            # ==========================================================

            respuesta = respuesta.strip()

            respuesta_enviada = False

            if respuesta.startswith("INTENT:"):

                lineas = respuesta.splitlines()

                intent_llm = (
                    lineas[0]
                    .replace("INTENT:", "")
                    .strip()
                )

                if (
                    intent_llm == "solicitar_autenticacion"
                    and flow != self.FLOW_ACADEMIC
                ):

                    logger.info(
                        "[LLM] Intent autenticación detectado."
                    )

                texto = "\n".join(
                    lineas[1:]
                ).strip()

                if texto:
                    dispatcher.utter_message(text=texto)
                    respuesta_enviada = True

                logger.info(
                    "[LLM] Intent detectado: %s",
                    intent_llm,
                )

            else:

                dispatcher.utter_message(
                    text=respuesta
                )
                respuesta_enviada = True

            if respuesta_enviada:
                logger.info(
                    "[LLM] Respuesta enviada correctamente."
                )
            # ==========================================================
            # CONTINUIDAD DEL FLUJO ACADÉMICO
            # ==========================================================

            if flow == self.FLOW_ACADEMIC:

                return [
                    FollowupAction(
                        "action_ofrecer_continuar_tema"
                    )
                ]

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

            # ==========================================================
            # TELEMETRÍA: MEDIDOR DE TIEMPO DE EJECUCIÓN
            # ==========================================================
            inicio_guardado = time.perf_counter()

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

            fin_guardado = time.perf_counter()
            tiempo_total = fin_guardado - inicio_guardado

            logger.info(
                "[MEMORY_WRAPPER] Mapeo de persistencia completado con éxito. "
                "Tiempo de ejecución de store_message: %.4f segundos.",
                tiempo_total
            )
            # ==========================================================

        except Exception:

            logger.exception(
                "[MEMORY_WRAPPER] Error durante la persistencia"
            )

        # Retorna lista vacía para preservar intactos los slots del flujo académico
        return []