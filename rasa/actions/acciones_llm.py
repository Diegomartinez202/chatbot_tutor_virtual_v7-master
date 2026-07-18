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
import traceback
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
        
        logger.info(
            "[LLM] _build_prompt() intent=%s",
            tracker.get_intent_of_latest_message(),
        )
        logger.warning(
            "[TRACE][ActionHandleWithLLM] llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        flow = self._detect_flow(tracker)

        logger.info(
            "[LLM] Flow detectado: %s",
            flow,
        )

        if flow == self.FLOW_AUTH:
            return self._build_auth_prompt(tracker)

        if flow == self.FLOW_ACADEMIC:

            intent = tracker.get_intent_of_latest_message()

            if intent in (
                "continuar_tema",
                "continuar_tema_si",
            ):
                logger.info("[LLM] Builder seleccionado=_build_continue_prompt")
                return self._build_continue_prompt(tracker)

            logger.info("[LLM] Builder seleccionado=_build_academic_prompt")
            return self._build_academic_prompt(tracker)

            return self._build_academic_prompt(tracker)

        if flow == self.FLOW_HELP:
            return self._build_help_prompt(tracker)
        
        elif flow == self.FLOW_SUPPORT:

            return self._build_support_prompt(tracker)

        if flow == self.FLOW_GENERAL:

            llm_request = tracker.get_slot("llm_request") or {}

            flujo = (
                llm_request
                .get("context", {})
                .get("flujo")
            )

            if flujo == "guardian_encuesta":
                return self._build_guardian_encuesta_prompt(tracker)

            if flujo == "cierre_conversacion":
                return self._build_cierre_prompt(tracker)

        return self._build_general_prompt(tracker)

    def _build_guardian_encuesta_prompt(
        self,
        tracker: Tracker,
    ) -> str:

        llm_request = tracker.get_slot("llm_request") or {}

        return llm_request.get(
            "instruction",
            "",
        )

    def _build_cierre_prompt(
        self,
        tracker: Tracker,
    ) -> str:

        llm_request = tracker.get_slot("llm_request") or {}

        return llm_request.get(
            "instruction",
            "",
        )
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

            1. Macroflujo definido por el orquestador (llm_request)
            2. Flujos especiales (cierre / encuesta)
            3. Académico
            4. Autenticación
            5. Soporte
            6. Ayuda
            7. General

        Mantiene compatibilidad con la arquitectura actual mientras
        se migran progresivamente todos los subflujos.
        """

        latest = tracker.latest_message or {}

        intent = (
            latest.get("intent", {})
            .get("name", "")
        )

        llm_request = tracker.get_slot("llm_request") or {}

        request_context = llm_request.get(
            "context",
            {},
        )

        macroflujo = request_context.get(
            "macroflujo"
        )

        subflujo = request_context.get(
            "subflujo"
        )

        # ======================================================
        # PRIORIDAD 1
        # NUEVA ARQUITECTURA (macroflujo / subflujo)
        # ======================================================

        if macroflujo:

            logger.info(
                "[FLOW] Macroflujo=%s | Subflujo=%s",
                macroflujo,
                subflujo,
            )

            if macroflujo == "academic":
                return self.FLOW_ACADEMIC

            if macroflujo == "support":
                return self.FLOW_SUPPORT

            if macroflujo == "auth":
                return self.FLOW_AUTH

            if macroflujo == "help":
                return self.FLOW_HELP

            if macroflujo == "general":
                return self.FLOW_GENERAL

        # ======================================================
        # COMPATIBILIDAD CON FLUJOS ANTIGUOS
        # ======================================================

        flujo = request_context.get("flujo")

        if flujo in (
            "guardian_encuesta",
            "cierre_conversacion",
        ):

            logger.info(
                "[FLOW] Flujo especial=%s",
                flujo,
            )

            return self.FLOW_GENERAL

        if flujo == "auth_required":
            return self.FLOW_AUTH

        if flujo == "support":
            return self.FLOW_SUPPORT

        # ======================================================
        # FLUJOS DE CIERRE
        # ======================================================

        if tracker.get_slot("esperando_encuesta_general"):
            return self.FLOW_GENERAL

        if tracker.get_slot("encuesta_activa"):
            return self.FLOW_GENERAL

        if tracker.get_slot("confirmacion_cierre"):
            return self.FLOW_GENERAL

        # ======================================================
        # FLUJO ACADÉMICO
        # ======================================================

        proceso = tracker.get_slot("proceso_activo")

        tema = tracker.get_slot("tema_consulta")

        materia = tracker.get_slot("materia_detectada")

        esperando = tracker.get_slot(
            "esperando_tema"
        )

        logger.debug(
            "[FLOW] proceso=%s tema=%s materia=%s",
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

            logger.info(
                "[FLOW] Flujo académico detectado."
            )

            return self.FLOW_ACADEMIC

        # ======================================================
        # AYUDA
        # ======================================================

        if intent == "ayuda":
            return self.FLOW_HELP

        # ======================================================
        # GENERAL
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
        Construye el prompt académico según el estado del
        aprendizaje.

        Casos:

        1. Primera explicación del tema.
        2. Profundización sobre un subtema.
        3. Continuar aumentando el nivel del mismo tema.
        """

        latest = tracker.latest_message or {}

        pregunta = (
            tracker.get_slot("tema_consulta")
            or latest.get("text", "")
        ).strip()

        tema_principal = (
            tracker.get_slot("tema_actual")
            or pregunta
        )

        materia = (
            tracker.get_slot("materia_detectada")
            or detectar_materia(tema_principal)
            or "General"
        )

        rol = (
            tracker.get_slot("rol_academico")
            or MATERIAS.get(
                str(materia).lower(),
                "Tutor Académico General",
            )
        )

        continuando = tracker.get_slot(
            "continuando_tema"
        )

        logger.info("=" * 80)
        logger.info("USANDO _build_academic_prompt()")
        logger.info("tema_actual=%s", tema_principal)
        logger.info("tema_consulta=%s", pregunta)
        logger.info("continuando=%s", continuando)
        logger.info("=" * 80)

        # ======================================================
        # CONTINUAR TEMA
        # ======================================================

        if continuando:

            return f"""
    Eres {rol}.

    Continúa profundizando el siguiente tema.

    Tema principal:

    {tema_principal}

    No repitas la introducción.

    Asume que el estudiante ya comprendió la explicación anterior.

    Aumenta el nivel técnico.

    Incluye nuevos ejemplos.

    Relaciona la explicación con lo explicado anteriormente.

    No reinicies el tema.
    """.strip()

        # ======================================================
        # PRIMERA EXPLICACIÓN
        # ======================================================

        if pregunta == tema_principal:

            return f"""
    Eres {rol}.

    Explica el siguiente tema como un tutor especializado del SENA.

    Tema:

    {tema_principal}

    Incluye:

    - definición
    - conceptos principales
    - explicación paso a paso
    - ejemplos sencillos
    - buenas prácticas

    No asumas conocimientos previos.
    """.strip()

        # ======================================================
        # SUBCONSULTA
        # ======================================================

        return f"""
    Eres {rol}.

    El estudiante está aprendiendo actualmente el siguiente tema:

    {tema_principal}

    Ahora realizó una nueva consulta:

    {pregunta}

    Primero determina si esta nueva consulta:

    - pertenece al mismo tema,
    - está relacionada parcialmente,
    - o corresponde a un tema completamente diferente.

    Si pertenece al mismo tema:

    Explica únicamente ese subtema y relaciónalo naturalmente con el tema principal.

    Si está parcialmente relacionada:

    Antes de explicar, escribe un breve párrafo de transición indicando cómo se relaciona con el tema principal.

    Después continúa con la explicación.

    Si corresponde a un tema diferente:

    Comienza con un breve párrafo indicando que la nueva consulta cambia el enfoque del aprendizaje.

    Luego explica completamente el nuevo tema.

    No repitas la explicación anterior.

    No reinicies el tema principal salvo que sea necesario.

    Mantén un tono de tutor académico del SENA.
    """.strip()

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
         Construye el contexto estructurado enviado al Prompt Builder.

         El contexto depende del macroflujo.

         No todos los flujos requieren información académica.

         Mantiene compatibilidad con la arquitectura actual.
         """

         latest = tracker.latest_message or {}

         intent = latest.get(
             "intent",
             {},
         ) or {}

         llm_request = tracker.get_slot(
             "llm_request"
         ) or {}

         request_context = llm_request.get(
             "context",
             {},
         )

         macroflujo = (
             request_context.get("macroflujo")
             or flow
         )

         subflujo = (
             request_context.get("subflujo")
             or request_context.get("flujo")
             or ""
         )

         context = {

             "macroflujo": macroflujo,

             "subflujo": subflujo,

             "flujo": flow,

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

         # ======================================================
         # CONTEXTO ACADÉMICO
         # ======================================================

         if macroflujo in (
             "academic",
             self.FLOW_ACADEMIC,
         ):

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

             context.update(

                 {

                     "materia": materia,

                     "rol": rol,

                     "tema_consulta": tracker.get_slot(
                     "tema_consulta"
                     ),

                     "nivel_explicacion": tracker.get_slot(
                     "nivel_explicacion"
                     ),

                 }

             )

         # ======================================================
         # CONTEXTO SOPORTE
         # ======================================================

         elif macroflujo in (
             "support",
             self.FLOW_SUPPORT,
         ):

             context.update(

                 {

                     "ticket": tracker.get_slot(
                         "ticket_id"
                     ),

                     "proceso": tracker.get_slot(
                         "proceso_activo"
                     ),

                 }

             )

         # ======================================================
         # CONTEXTO AUTENTICACIÓN
         # ======================================================

         elif macroflujo in (
             "auth",
             self.FLOW_AUTH,
         ):

             context.update(

                 {

                     "auth_state": tracker.get_slot(
                         "auth_state"
                     ),

                     "is_authenticated": tracker.get_slot(
                         "is_authenticated"
                     ),

                 }

             )

         # ======================================================
         # CONTEXTO GENERAL
         # ======================================================

         logger.info(
             "[LLM CONTEXT] macroflujo=%s | subflujo=%s",
             macroflujo,
             subflujo,
         )

         return context

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
        logger.info(
            "[ACADEMICO] Desactivando esperando_tema"
        )
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

            SlotSet("llm_request", None),

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
        Construye un prompt enriquecido para continuar una
        explicación ya iniciada aprovechando el contexto de
        la última respuesta generada por el LLM.
        """
        logger.info("=" * 70)
        logger.info("[LLM] USANDO _build_continue_prompt()")
        logger.info("tema_actual=%s", tracker.get_slot("tema_actual"))
        logger.info("tema_consulta=%s", tracker.get_slot("tema_consulta"))
        logger.info("nivel=%s", tracker.get_slot("nivel_explicacion"))
        logger.info("ultima_respuesta=%s", bool(tracker.get_slot("ultima_respuesta_llm")))
        logger.info("=" * 70)
       
        tema = (
            tracker.get_slot("tema_actual")
            or tracker.get_slot("tema_consulta")
            or "el tema anterior"
        )

        nivel = (
            tracker.get_slot("nivel_explicacion")
            or "basico"
        )

        ultima_respuesta = (
            tracker.get_slot("ultima_respuesta_llm")
            or ""
        ).strip()
        if len(ultima_respuesta) > 1200:
            ultima_respuesta = ultima_respuesta[-1200:]
        prompt = f"""
    Continúa explicando el siguiente tema académico.

    Tema:

    {tema}

    Nivel actual de explicación:

    {nivel}

    IMPORTANTE:

    El estudiante NO está iniciando un tema nuevo.

    Ya recibió una explicación inicial sobre este mismo tema.

    Esta conversación es una continuación directa de la explicación anterior.

    NO preguntes qué desea aprender.

    NO preguntes qué concepto desea explicar.

    NO solicites aclaraciones.

    NO vuelvas a empezar desde la definición.

    NO repitas la introducción.

    NO vuelvas a explicar conceptos que ya fueron desarrollados.

    NO reinicies la explicación.

    NO respondas como si fuera una consulta nueva.

    Continúa exactamente desde donde terminó la explicación anterior.
    """

        if ultima_respuesta:

            prompt += f"""

    Profundiza el tema de acuerdo con el nivel:

    {ultima_respuesta}

    Usa esa explicación únicamente como contexto para continuar.

    No la copies.

    No la repitas.

    Continúa desde el último punto desarrollado.
    """

        prompt += f"""

    Profundiza el tema de acuerdo con el nivel:

    {nivel}

    Incluye, cuando sea pertinente:

    - conceptos más avanzados
    - detalles técnicos
    - relaciones con otros conceptos
    - ejemplos nuevos
    - casos prácticos
    - errores comunes
    - recomendaciones
    - buenas prácticas
    - un ejercicio corto con solución

    Mantén continuidad pedagógica como si la conversación nunca se hubiera interrumpido.

    Comienza inmediatamente ampliando la explicación.

    No hagas preguntas.

    No solicites que el estudiante elija un tema.

    No pidas confirmación.

    Finaliza únicamente cuando hayas desarrollado la continuación del tema.
    """
        logger.info("=" * 70)
        logger.info("[LLM] Prompt CONTINUE")
        logger.info(prompt)
        logger.info("=" * 70)
        return prompt.strip()
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
        logger.warning(
            "[FLOW FINAL] parametro=%s | contexto=%s",
            flow,
            context.get("flujo"),
        )
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

        logger.warning(
            "[TRACE][ActionHandleWithLLM] llm_request=%s",
            tracker.get_slot("llm_request"),
        )

        flow = self._detect_flow(tracker)
        logger.info("[DEBUG] Flow detectado = %s", flow)
        intent = tracker.get_intent_of_latest_message()

        # ======================================================
        # CONTINUAR TEMA (PRIORIDAD)
        # ======================================================

        if intent in (
            "continuar_tema",
            "continuar_tema_si",
        ):

            logger.info("=" * 70)
            logger.info("[ACADEMICO] CONTINUAR TEMA")
            logger.info("tema_actual=%s", tracker.get_slot("tema_actual"))
            logger.info("tema_consulta=%s", tracker.get_slot("tema_consulta"))
            logger.info("nivel=%s", tracker.get_slot("nivel_explicacion"))
            logger.info(
                "ultima_respuesta=%s",
                bool(tracker.get_slot("ultima_respuesta_llm")),
            )
            logger.info("esperando_tema=%s", tracker.get_slot("esperando_tema"))
            logger.info("=" * 70)

            return (
                limpieza
                + self._ejecutar_procesamiento_llm(
                    dispatcher,
                    tracker,
                    self.FLOW_ACADEMIC,
                    prompt=self._build_continue_prompt(tracker),
                )
            )
        # ======================================================
        # MODO APRENDIZAJE
        # El usuario ya tiene un tema activo.
        # Cualquier texto nuevo se interpreta como una
        # profundización (subconsulta) del mismo tema.
        # ======================================================

        if (
            tracker.get_slot("proceso_activo") == "aprender_tema"
            and not tracker.get_slot("esperando_tema")
            and tracker.latest_message.get("text", "").strip()
            and intent not in (
                "continuar_tema",
                "continuar_tema_si",
                "ir_menu_principal",
                "terminar_conversacion_segura",
            )
        ):

            logger.info(
                "[ACADEMICO] Subconsulta detectada."
            )

            subtema = tracker.latest_message["text"].strip()

            logger.info(
                "[ACADEMICO] Tema principal=%s | Subtema=%s",
                tracker.get_slot("tema_actual"),
                subtema,
            )

            return (

                limpieza

                + [

                    # Solo cambia el foco de la consulta.
                    # El tema principal permanece igual.
                    SlotSet(
                        "tema_consulta",
                        subtema,
                    ),

                ]

                + self._ejecutar_procesamiento_llm(

                    dispatcher,

                    tracker,

                    self.FLOW_ACADEMIC,

                )

            )


        logger.info(
            "[DEBUG] esperando_tema=%s",
            tracker.get_slot("esperando_tema"),
        )

        # ======================================================
        # ESPERANDO QUE EL USUARIO ESCRIBA EL TEMA
        # Primera explicación del flujo académico.
        # Este es el único lugar donde se inicializa
        # tema_actual.
        # ======================================================

        if self._is_waiting_for_topic(tracker):

            nuevo_tema = tracker.latest_message.get(
                "text",
                "",
            ).strip()

            logger.info(
                "[ACADEMICO] Tema inicial recibido: %s",
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
        logger.info("=" * 70)
        logger.info("[LLM] _ejecutar_procesamiento_llm")
        logger.info("flow=%s", flow)
        logger.info("prompt recibido=%s", prompt[:120] if prompt else None)
        logger.info("=" * 70)
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

                context_llm = llm_request.get("context", {})
                flujo_llm = context_llm.get("flujo")

               # Para flujos especiales NO reutilizamos el contexto académico
                if flujo_llm in (
                    "guardian_encuesta",
                ):
                    context = dict(context_llm)

                else:

                    context = self._build_llm_context(
                        tracker,
                        flow,
                    )

                    context.update(context_llm)

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

            logger.info("=" * 70)
            logger.info("[LLM] Prompt FINAL")
            logger.info(prompt)
            logger.info("=" * 70)
            prompt = build_prompt(
                base_prompt=prompt,
                tracker=tracker,
                context=context,
            )
            logger.info("=" * 70)
            logger.info("[LLM] Prompt FINAL")
            logger.info(prompt)
            logger.info("=" * 70)
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

                    SlotSet("ultima_respuesta_llm", None),

                    FollowupAction(next_action),

                ]

            # =====================================================
            # Continuación normal del flujo
            # =====================================================

            events = self._build_followup_events(
                flow,
            )

            # -----------------------------------------------------
            # Mantener proceso_activo SOLO para soporte.
            #
            # El flujo académico utiliza "aprender_tema".
            # No debe sobrescribirse con "academic",
            # porque rompe la lógica conversacional.
            # -----------------------------------------------------

            if flow == self.FLOW_SUPPORT:

                events.insert(
                    0,
                    SlotSet(
                        "proceso_activo",
                        "support",
                    ),
                )

            # -----------------------------------------------------
            # Flujo académico
            # -----------------------------------------------------

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

        
        logger.warning(
            "[MEMORY_WRAPPER] Ejecutado. intent=%s sender=%s",
            tracker.get_intent_of_latest_message(),
            tracker.sender_id,
        )
        logger.warning(
            "".join(traceback.format_stack(limit=8))
        )
        logger.warning("=" * 80)
        logger.warning("[MEMORY_WRAPPER] EJECUTADO")
        logger.warning("intent=%s", tracker.get_intent_of_latest_message())
        logger.warning("sender=%s", tracker.sender_id)
        logger.warning("stack:")
        logger.warning("".join(traceback.format_stack(limit=8)))
        logger.warning("=" * 80)
        logger.debug(
            "[MEMORY_WRAPPER] Persistiendo conversación"
        )

        try:
            latest = tracker.latest_message or {}

            text = str(
                latest.get("text") or ""
            ).strip()

            if not text:
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