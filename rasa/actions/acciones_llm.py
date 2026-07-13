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
from datetime import datetime
# ---------------------------------------------------------------------
# Memoria semántica
# ---------------------------------------------------------------------

from .actions_semantic_memory import (
    store_message,
)

# ---------------------------------------------------------------------
# Motor LLM
# ---------------------------------------------------------------------

from .core.llm_engine import run_llm

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
    build_prompt,
    PROMPT_SYSTEM,
)
from .core.history import build_history
from .core.materias import MATERIAS
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
        
        elif flow == self.FLOW_SUPPORT:

            return self._build_support_prompt(tracker)

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

        latest = tracker.latest_message or {}

        intent = (
            latest.get("intent", {})
            .get("name", "")
        )

        # ======================================================
        # 1. FLUJO ACADÉMICO
        # ======================================================
        # Si ya existe una consulta académica en curso,
        # siempre debe tener prioridad sobre un estado
        # antiguo de autenticación.

        proceso = tracker.get_slot("proceso_activo")
        tema = tracker.get_slot("tema_consulta")
        materia = tracker.get_slot("materia_detectada")
        esperando = tracker.get_slot(
            "esperando_tema"
        )
        logger.debug(
            "[FLOW] proceso_activo=%s | tema=%s | materia=%s",
            proceso,
            bool(tema),
            bool(materia),
        )

        if (
            esperando
            or proceso == "aprender_tema"
            or tema
            or materia
        ):
            logger.info("[FLOW] Flujo académico detectado.")
            return self.FLOW_ACADEMIC

        # ======================================================
        # 2. AUTENTICACIÓN
        # ======================================================

        llm_request = tracker.get_slot("llm_request") or {}

        context = llm_request.get("context", {})

        if context.get("flujo") == "auth_required":
            return self.FLOW_AUTH

        # ======================================================
        # 3. SOPORTE
        # ======================================================

        if context.get("flujo") == "support":
            return self.FLOW_SUPPORT

        # ======================================================
        # 4. AYUDA
        # ======================================================

        if intent == "ayuda":
            return self.FLOW_HELP

        # ======================================================
        # 5. GENERAL
        # ======================================================

        return self.FLOW_GENERAL
    # ======================================================
    # BUILDERS ESPECIALIZADOS
    # ==========================================================

    def _build_auth_prompt(
       self,
       tracker: Tracker,
    ) -> str:
       """
       Devuelve únicamente la acción protegida que intentó realizar
       el usuario.

       build_prompt() será el encargado de construir el prompt final
       utilizando el flujo "auth".
       """

       llm_request = tracker.get_slot("llm_request") or {}

       context = llm_request.get(
           "context",
           {},
       )

       return context.get(
           "pending_action",
           "consultar información personal",
       )

    def _build_academic_prompt(
        self,
        tracker: Tracker,
    ) -> str:
        """
        Devuelve únicamente la consulta académica realizada por el
        estudiante.

        build_prompt() será el único responsable de construir el
        prompt final.
        """
        latest = tracker.latest_message or {}
        pregunta = (
            tracker.get_slot("tema_consulta")
            or latest.get("text", "")
        ).strip()


        materia = (
            tracker.get_slot("materia_detectada")
            or detectar_materia(pregunta)
            or "General"
        )

        rol = (
            tracker.get_slot("rol_academico")
            or MATERIAS.get(
                str(materia).lower(),
                "Tutor Académico General",
            )
        )

        if not tracker.get_slot("materia_detectada"):

            logger.debug(
                "[LLM] Materia detectada automáticamente: %s",
                materia,
            )

        if not tracker.get_slot("rol_academico"):

            logger.debug(
                "[LLM] Rol académico seleccionado: %s",
                rol,
            )

        return pregunta


    # ==========================================================
    # HELP PROMPT
    # ==========================================================

    def _build_help_prompt(
        self,
        tracker: Tracker,
    ) -> str:
        """
        Devuelve únicamente la consulta del usuario.

        build_prompt() añadirá las instrucciones del flujo help.
        """
        latest = tracker.latest_message or {}

        return latest.get(
            "text",
            "",
        ).strip() or "El usuario solicita ayuda."


    # ==========================================================
    # GENERAL PROMPT
    # ==========================================================

    def _build_general_prompt(
        self,
        tracker: Tracker,
    ) -> str:
        """
        Devuelve únicamente el mensaje del usuario.

        Todo el contexto será agregado posteriormente por
        build_prompt().
        """

        latest = tracker.latest_message or {}

        return anonymize_text(
            latest.get(
                "text",
                "",
            ).strip()
        )


    # ==========================================================
    # CONTEXTO PARA EL LLM
    # ==========================================================

    def _build_llm_context(
        self,
        tracker: Tracker,
        flow: str,
    ) -> Dict[str, Any]:
        """
        Construye el contexto estructurado que utilizará build_prompt().

        Este método NO genera prompts.
        Únicamente recopila información del flujo.
        """

        latest = tracker.latest_message or {}
        intent = latest.get("intent", {}) or {}

        pregunta = (
            tracker.get_slot("tema_consulta")
            or latest.get("text", "")
        )

        materia = (
            tracker.get_slot("materia_detectada")
            or detectar_materia(pregunta)
            or "General"
        )

        rol = (
            tracker.get_slot("rol_academico")
            or MATERIAS.get(
                str(materia).lower(),
                "Tutor Académico General",
            )
        )

        llm_request = tracker.get_slot("llm_request") or {}

        request_context = llm_request.get(
            "context",
            {},
        )

        return {

            "flujo": flow,

            "materia": materia,
            "rol": rol,

            "intent": intent.get(
                "name",
                "desconocido",
            ),

            "confidence": intent.get(
                "confidence",
                0.0,
            ),

            "session_id": tracker.get_slot(
                "session_id",
            ),

            "pending_action": request_context.get(
                "pending_action",
                "",
            ),

            "auth_required": request_context.get(
                "requires_auth",
                False,
            ),

        }

    # ==========================================================
    # SUPPORT PROMPT
    # ==========================================================

    def _build_support_prompt(
        self,
        tracker: Tracker,
    ) -> str:
        """
        Devuelve únicamente el problema reportado por el usuario.

        build_prompt() añadirá posteriormente el historial,
        memoria, contexto e instrucciones específicas del flujo
        support.
        """
 
        latest = tracker.latest_message or {}

        return latest.get(
            "text",
            "",
        ).strip() or "El usuario reporta un problema."

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
    
    def _is_waiting_for_topic(
        self,
        tracker: Tracker,
    ) -> bool:
        """
        Indica si el bot se encuentra esperando que el usuario escriba
        el tema que desea aprender.
        """

        return bool(
            tracker.get_slot("esperando_tema")
        )
    
    def _build_topic_events(
        self,
        tracker: Tracker,
    ) -> List[EventType]:
        """
        Inicializa el flujo académico cuando el usuario escribe
        el tema solicitado.
        """

        latest = tracker.latest_message or {}

        tema = latest.get(
            "text",
            "",
        ).strip()
        materia = detectar_materia(tema) or "General"

        rol = MATERIAS.get(
            materia.lower(),
            "Tutor Académico General"
        )
        return [

            SlotSet(
                "esperando_tema",
                False,
            ),

            SlotSet(
                "tema_actual",
                tema,
            ),

            SlotSet(
                "tema_consulta",
                tema,
            ),

            SlotSet(
                "proceso_activo",
                "aprender_tema",
            ),
            SlotSet(
               "materia_detectada",
               materia,
            ),

            SlotSet(
                "rol_academico",
                rol,
            ),

        ]

    def _build_continue_prompt(
        self,
        tracker: Tracker,
    ) -> str:
        """
        Construye un prompt enriquecido para continuar
        una explicación ya iniciada.
        """

        tema = (
            tracker.get_slot("tema_actual")
            or tracker.get_slot("tema_consulta")
            or "el tema anterior"
        )
        nivel = (
            tracker.get_slot("nivel_explicacion")
            or "basico"
        )

        return f"""
    Tema actual:

    {tema}

    Nivel de explicación:

    {nivel}

    El estudiante ya recibió una explicación inicial.

    Continúa exactamente desde donde terminó.

    No repitas la introducción.

    No saludes nuevamente.

    Profundiza el tema.

    Adapta la explicación al nivel {nivel}.

    Incluye ejemplos prácticos.

    Si aplica agrega un ejercicio corto.

    Mantén continuidad pedagógica.
    """.strip()
    
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
        Invoca el motor LLM.

        El prompt YA viene completamente construido desde
        _ejecutar_procesamiento_llm().
 
        Esta función únicamente delega la ejecución al motor LLM.
        """

        logger.info(
            "[LLM] Preparando prompt para flujo '%s'",
            flow,
        )

        logger.debug(
            "[LLM] Prompt final construido (%d caracteres)",
            len(prompt),
        )
        logger.debug(
        "[LLM] Prompt enviado:\n%s",
        prompt,
        )
        return run_llm(
            prompt=prompt,
            tracker=tracker,
            context=context,
            fallback=fallback,
            dispatcher=dispatcher,
        )
       
    def run(
        self,
        dispatcher,
        tracker,
        domain,
    ) -> List[EventType]:

        logger.info("=" * 80)
        logger.info("[DEBUG ACTION_HANDLE_WITH_LLM]")
        logger.info("intent=%s", tracker.get_intent_of_latest_message())
        logger.info("llm_request=%s", tracker.get_slot("llm_request"))
        logger.info("proceso_activo=%s", tracker.get_slot("proceso_activo"))
        logger.info("tema_consulta=%s", tracker.get_slot("tema_consulta"))
        logger.info("materia_detectada=%s", tracker.get_slot("materia_detectada"))
        logger.info("=" * 80)

        limpieza = [
            ActiveLoop(None),
            SlotSet("requested_slot", None),
        ]

        flow = self._detect_flow(tracker)
        logger.info("[DEBUG] Flow detectado = %s", flow)
        intent = tracker.get_intent_of_latest_message()


        # ======================================================
        # ESPERANDO QUE EL USUARIO ESCRIBA EL TEMA
        # ======================================================

        if self._is_waiting_for_topic(tracker):

            nuevo_tema = tracker.latest_message.get(
                "text",
                "",
            ).strip()

            logger.info(
                "[ACADEMICO] Tema recibido: %s",
                nuevo_tema,
            )

            return (

                limpieza

                + self._build_topic_events(
                   tracker
                )

                + self._ejecutar_procesamiento_llm(

                    dispatcher,

                    tracker,

                    self.FLOW_ACADEMIC,

                    prompt=nuevo_tema,

                )

            )
        # ======================================================
        # CONSULTA ACADÉMICA NUEVA
        # ======================================================

        if intent == "explicacion_academica":

            nuevo_tema = tracker.latest_message.get("text")

            return (
                limpieza
                + [
                    SlotSet("tema_actual", nuevo_tema),
                ]
                + self._ejecutar_procesamiento_llm(
                    dispatcher,
                    tracker,
                    self.FLOW_ACADEMIC,
                )
            )

        # ======================================================
        # CONTINUAR TEMA
        # ======================================================

        if intent in (

            "continuar_tema",

            "continuar_tema_si",

        ):

            logger.info(
                "[ACADEMICO] Continuando tema."
            )

            return self._ejecutar_procesamiento_llm(

                dispatcher,

                tracker,

                flow,

                prompt=self._build_continue_prompt(
                    tracker
                ),

            )

        # ======================================================
        # FLUJO NORMAL
        # ======================================================

        return (
            limpieza
            + self._ejecutar_procesamiento_llm(
                dispatcher,
                tracker,
               flow,
            )
        )
    
    def _next_explanation_level(
        self,
        tracker: Tracker,
    ) -> str:

        actual = tracker.get_slot(
            "nivel_explicacion"
        )

        niveles = [

            "basico",

            "intermedio",

            "avanzado",

            "ejercicios",

            "evaluacion",

        ]

        if actual not in niveles:

            return "basico"

        indice = niveles.index(actual)

        if indice < len(niveles) - 1:

            return niveles[indice + 1]

        return niveles[-1]

    def _ejecutar_procesamiento_llm(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        flow: str,
        prompt: str | None = None,
    ) -> List[EventType]:
        """
        Orquesta todo el procesamiento del LLM.

        Arquitectura:

            builder específico
                ↓
           build_prompt()
                ↓
           run_llm()
                ↓
           _call_model()
        """

        logger.info(
            "[DEBUG LLM] llm_request=%s",
            tracker.get_slot("llm_request"),
        )

        try:

            llm_request = tracker.get_slot("llm_request") or {}

            logger.info(
                "[DEBUG] llm_request=%s",
                llm_request,
            )

            # ==================================    ===================
            # Obtener contenido del flujo
            # =====================================================

            if llm_request:

                if prompt is None:

                    prompt = llm_request.get(
                        "instruction",
                        "",
                    )

                # -------------------------------------------------
                # Construir siempre el contexto base del flujo
                # -------------------------------------------------

                context = self._build_llm_context(
                    tracker,
                    flow,
                )

                # -------------------------------------------------
                # Sobrescribir únicamente los datos específicos
                # enviados por llm_request
                # -------------------------------------------------

                context.update(

                    llm_request.get(
                        "context",
                        {},
                    )

                )

                fallback = llm_request.get(
                    "fallback",
                    "Lo siento, no puedo responder en este momento.",
                )

            else:

                if prompt is None:

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



            # =====================================================
            # Construir SIEMPRE el prompt final
            # =====================================================
            logger.info(
                "[PROMPT] base=%d caracteres",
                len(prompt),
            )


            prompt = build_prompt(
                base_prompt=prompt,
                tracker=tracker,
                context=context,
            )
            logger.info(
                "[PROMPT] final=%d caracteres",
                len(prompt),
            )
            logger.debug(
                "[LLM] Prompt final (%d caracteres)",
                len(prompt),
            )

            # =====================================================
            # Invocar LLM
            # =====================================================

            respuesta = self._invoke_llm(
                dispatcher=dispatcher,
                tracker=tracker,
                prompt=prompt,
                flow=flow,
                context=context,
                fallback=fallback,
            )

            respuesta = (respuesta or "").strip()
            logger.info(
                "[LLM] Primeros 200 caracteres de la respuesta:\n%s",
                respuesta[:200],
            )
            # =====================================================
            # Respuesta vacía
            # =====================================================

            if not respuesta:

                dispatcher.utter_message(
                    text=fallback,
                )

                return [
                    SlotSet(
                        "llm_request",
                        None,
                    ),
                ]

            # =====================================================
            # Intent devuelto por el LLM
            # =====================================================

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

                logger.info(
                    "[LLM] Intent detectado=%s",
                    intent_llm,
                )

            else:

                dispatcher.utter_message(
                    text=respuesta,
                )

            logger.info(
                "[LLM] Respuesta enviada.",
            )

            # =====================================================
            # Acción posterior definida por llm_request
            # =====================================================

            next_action = llm_request.get(
                "next_action",
            )

            if next_action:
                return [

                    ActiveLoop(None),

                    SlotSet("requested_slot", None),

                    SlotSet("llm_request", None),

                    FollowupAction(next_action),

                ]

            # =====================================================
            # Continuación normal del flujo
            # =====================================================

            events = self._build_followup_events(
                flow,
            )

            if flow in (
                self.FLOW_ACADEMIC,
                self.FLOW_SUPPORT,
            ):

                events.insert(
                     0,
                     SlotSet(
                         "proceso_activo",
                         flow,
                     ),
                )


            if flow == self.FLOW_ACADEMIC:

                events.extend(

                   [

                      SlotSet(
                          "ultima_respuesta_llm",
                          respuesta,
                      ),

                      SlotSet(
                         "ultima_interaccion",
                         datetime.utcnow().isoformat(),
                      ),

                   ]

                )

                events.append(

                    SlotSet(

                        "nivel_explicacion",

                        self._next_explanation_level(
                            tracker
                        ),

                    )

                )


            return events

        except Exception:

            logger.exception(
                "[ACTION_HANDLE_WITH_LLM] Error inesperado",
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