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
    FLOW_SUPPORT = "support"
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
    Determina el macroflujo conversacional.

    Prioridad:

        1. Académico
        2. Autenticación
        3. Soporte
        4. Ayuda
        5. General

    Los subflujos (PQRS, certificados, correo,
    soporte técnico, etc.) permanecen dentro del
    contexto del LLM y no modifican el flujo principal.
    """

    # ======================================================
    # 1. FLUJO ACADÉMICO
    # ======================================================

    es_academico = bool(

        tracker.get_slot("tema_consulta")
        or tracker.get_slot("materia_detectada")

    )

    if es_academico:
        return self.FLOW_ACADEMIC

    # ======================================================
    # 2. AUTENTICACIÓN
    # ======================================================

    if tracker.get_slot("requires_auth"):
        return self.FLOW_AUTH

    # ======================================================
    # 3. SOPORTE
    # ======================================================

    llm_request = tracker.get_slot("llm_request") or {}

    context = llm_request.get("context", {})

    if context.get("flujo") == "support":
        return self.FLOW_SUPPORT

    # ======================================================
    # 4. AYUDA
    # ======================================================

    latest = tracker.latest_message or {}

    intent = (

        latest.get("intent", {})
        .get("name", "")

    )

    if intent == "ayuda":
        return self.FLOW_HELP

    # ======================================================
    # 5. GENERAL
    # ======================================================

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
    def _build_history(self, tracker: Tracker, max_events: int = 2, max_lines: int = 2) -> str:
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
    # EVENTOS DE CONTINUIDAD DEL FLUJO
    # ==========================================================

    def _build_followup_events(
        self,
        flow: str,
    ) -> List[EventType]:
        """
        Construye los eventos de continuación del flujo una vez que
        la respuesta del LLM ha sido enviada al usuario.

        Centralizar esta lógica evita que _ejecutar_procesamiento_llm()
        siga creciendo cada vez que se agreguen nuevos macroflujos.
        """

        events: List[EventType] = [

            SlotSet(
                "llm_request",
                None,
            ),

        ]

        # ------------------------------------------------------
        # Flujo académico
        # ------------------------------------------------------

        if flow == self.FLOW_ACADEMIC:

            events.append(

                FollowupAction(
                    "action_ofrecer_continuar_tema"
                )

            )

        # ------------------------------------------------------
        # Flujo de soporte
        # ------------------------------------------------------

        elif flow == self.FLOW_SUPPORT:

            events.append(

                FollowupAction(
                    "action_preguntar_resolucion"
                )

            )

        # ------------------------------------------------------
        # Futuros flujos
        # ------------------------------------------------------
        #
        # elif flow == self.FLOW_CERTIFICADOS:
        #     ...
        #
        # elif flow == self.FLOW_MATRICULA:
        #     ...
        #
        # elif flow == self.FLOW_BIENESTAR:
        #     ...
        #
        # ------------------------------------------------------

        return events
# ==========================================================
# INVOCACIÓN DEL LLM
# ==========================================================

def _invoke_llm(
    self,
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    prompt: str,
    flow: str,
    context: Dict[str, Any],
    fallback: str,
) -> str:
    """
    Centraliza la invocación al motor LLM.

    Responsabilidades:

    • Construir el prompt final.
    • Incorporar historial cuando corresponda.
    • Recuperar memoria semántica.
    • Registrar el flujo lógico utilizado.
    • Invocar run_llm().

    Los subflujos (guardian_autosave, guardian_encuesta,
    handoff, pqrs, soporte, etc.) llegan mediante el
    parámetro 'context' y NO requieren crear nuevos FLOW_*.
    """

    # ------------------------------------------------------
    # Flujo principal
    # ------------------------------------------------------

    logger.info(
        "[LLM] Preparando prompt para flujo '%s'",
        flow,
    )

    # ------------------------------------------------------
    # Subflujo (si existe)
    # ------------------------------------------------------

    subflow = ""

    if isinstance(context, dict):
        subflow = context.get("flujo", "")

    if subflow:

        logger.debug(
            "[LLM] Subflujo detectado: %s",
            subflow,
        )

    # ------------------------------------------------------
    # Historial
    # ------------------------------------------------------

    history = (
        ""
        if flow == self.FLOW_ACADEMIC
        else self._build_history(tracker)
    )

    # ------------------------------------------------------
    # Mensaje del usuario
    # ------------------------------------------------------

    latest = tracker.latest_message or {}

    if flow == self.FLOW_ACADEMIC:

        user_message = (
            tracker.get_slot("tema_consulta")
            or latest.get("text", "")
        )

    else:

        user_message = latest.get(
            "text",
            "",
        )

    # ------------------------------------------------------
    # Memoria semántica
    # ------------------------------------------------------

    memory = ""

    if (
        flow != self.FLOW_ACADEMIC
        and user_message.strip()
    ):

        memory = self._recover_semantic_memory(
            tracker=tracker,
            text=user_message,
        )

    # ------------------------------------------------------
    # Construcción del prompt
    # ------------------------------------------------------

    if flow == self.FLOW_ACADEMIC:

        prompt_final = prompt

    else:

        prompt_final = PROMPT_TEMPLATE.format(

            history=(
                history
                or "Sin historial reciente."
            ),

            memory=(
                memory
                or "Sin contexto previo relevante."
            ),

            question=user_message,

            instructions=prompt,

        )

    # ------------------------------------------------------
    # Invocación centralizada
    # ------------------------------------------------------

    return run_llm(

        prompt=prompt_final,

        tracker=tracker,

        context=context,

        fallback=fallback,

        dispatcher=dispatcher,

    )
       
    def run(self, dispatcher, tracker, domain) -> List[EventType]:
        limpieza = [ActiveLoop(None), SlotSet("requested_slot", None)]
        flow = self._detect_flow(tracker)
        
        intent = tracker.get_intent_of_latest_message()
        
       
        if intent == "explicacion_academica":
         
            nuevo_tema = tracker.latest_message.get("text")
            return limpieza + [SlotSet("tema_actual", nuevo_tema)] + self._ejecutar_procesamiento_llm(dispatcher, tracker, self.FLOW_ACADEMIC)

      
        if intent == "continuar_tema":
            tema_persistido = tracker.get_slot("tema_actual") or "el tema anterior"
            prompt_enriquecido = f"Contexto: {tema_persistido}. Continúa con el siguiente paso lógico. NO saludes, no repitas la introducción, ve directo al grano."
            return self._ejecutar_procesamiento_llm(dispatcher, tracker, flow, prompt=prompt_enriquecido)

        return limpieza + self._ejecutar_procesamiento_llm(dispatcher, tracker, flow)
    
    
    def _ejecutar_procesamiento_llm(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        flow: str,
    ) -> List[EventType]:
        """
        Procesa la interacción con el LLM.

        Responsabilidades:

        - Construir el prompt.
        - Invocar el LLM.
        - Interpretar la respuesta.
        - Enviar la respuesta al usuario.
        - Delegar la continuación del flujo.
        """

        try:

            llm_request = tracker.get_slot("llm_request")

            if llm_request:

                prompt = llm_request.get(
                    "instruction",
                    "",
                )

                context = llm_request.get(
                    "context",
                    {},
                )

                fallback = llm_request.get(
                    "fallback",
                    "Lo siento, no puedo responder en este momento.",
                )

            else:

                prompt = self._build_prompt(
                    tracker,
                )

                context = self._build_llm_context(
                    tracker,
                    flow,
                )

                fallback = (
                    "Lo siento, no puedo responder en este momento."
                )

            logger.debug(
                "[LLM] Prompt generado (%d caracteres)",
                len(prompt),
            )

            respuesta = self._invoke_llm(
                dispatcher=dispatcher,
                tracker=tracker,
                prompt=prompt,
                flow=flow,
                context=context,
                fallback=fallback,
            )

            # ======================================================
            # INTERPRETAR RESPUESTA DEL LLM
            # ======================================================

            respuesta = respuesta.strip()

            respuesta_enviada = False

            if respuesta.startswith("INTENT:"):

                lineas = respuesta.splitlines()

                intent_llm = (
                    lineas[0]
                    .replace("INTENT:", "")
                    .strip()
                )

                texto = "\n".join(
                    lineas[1:]
                ).strip()

                if texto:

                    dispatcher.utter_message(
                        text=texto,
                    )

                    respuesta_enviada = True

                logger.info(
                    "[LLM] Intent detectado: %s",
                    intent_llm,
                )

            else:

                dispatcher.utter_message(
                    text=respuesta,
                )

                respuesta_enviada = True

            if respuesta_enviada:

                logger.info(
                    "[LLM] Respuesta enviada correctamente."
                )

            llm_request = tracker.get_slot("llm_request") or {}
            next_action = llm_request.get("next_action")

            if next_action:

                return [

                    SlotSet(
                        "llm_request",
                        None,
                    ),

                    FollowupAction(
                        next_action,
                    ),

                ]
          
            # ======================================================
            # CONTINUACIÓN DEL FLUJO
            # ======================================================

            return self._build_followup_events(
                flow,
            )

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
                    "llm_request",
                    None,
                ),

                SlotSet(
                    "requires_auth",
                    None,
                ),

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