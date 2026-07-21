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
    FLOW_ADMINISTRATIVE = "administrative"

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


        if flow == self.FLOW_ADMINISTRATIVE:

            logger.info(
                "[LLM] Builder=_build_administrative_prompt"
            )

            return self._build_administrative_prompt(
               tracker
            )
        
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

            if macroflujo == "administrative":

                logger.info(
                    "[FLOW] Flujo administrativo detectado."
                )

                return self.FLOW_ADMINISTRATIVE

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
        # COMPATIBILIDAD CON LA ARQUITECTURA ANTERIOR
        # Se utiliza únicamente cuando el ACTION_CATALOG aún
        # no ha definido el macroflujo.
        # ======================================================
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

        
        
        cambio_tema = tracker.get_slot("cambio_tema")
    
        if cambio_tema:

           tema_anterior = (
               tracker.get_slot("tema_anterior")
               or "el tema anterior"
           )

           return f"""
        Eres {rol}.

        El estudiante venía aprendiendo sobre:

        {tema_anterior}

        Ahora ha decidido comenzar un tema diferente:

        {tema_principal}

        Esta consulta corresponde a un cambio de tema y NO es una continuación de la explicación anterior.

       Antes de iniciar la explicación escribe únicamente un breve párrafo de transición.

       La transición debe cumplir las siguientes reglas:

       - Reconoce de forma natural que el estudiante cambió de tema.
       - Si ambos temas tienen relación, menciona brevemente esa relación.
       - Si pertenecen a áreas distintas, indícalo de manera natural explicando que ambos forman parte del proceso de formación del SENA.
       - La transición debe ocupar un solo párrafo.
       - No hagas preguntas.
       - No repitas contenido del tema anterior.
       - Después de la transición comienza inmediatamente la explicación del nuevo tema desde el nivel básico.

       Ejemplos válidos de transición:

       "Ahora abordaremos un tema diferente que complementa tu proceso de aprendizaje."

       "Dejando atrás el tema anterior, comenzaremos a estudiar un nuevo concepto."

       "A continuación iniciaremos un tema distinto que también hace parte de tu formación."

       "Ahora cambiaremos de enfoque para aprender un nuevo tema."

       Después de ese único párrafo inicia inmediatamente la explicación de:

       {tema_principal}

       No vuelvas a mencionar el tema anterior durante el resto de la respuesta.

       La explicación debe ser clara, progresiva, didáctica y adecuada para un estudiante del SENA.
       """.strip()
        
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

    El estudiante está comenzando por primera vez este tema.

    Tema:

    {tema_principal}

    Desarrolla una explicación completa, pedagógica y estructurada.

    La explicación debe ser suficiente para que un estudiante que nunca ha visto el tema pueda comprenderlo.

    Organiza la respuesta en el siguiente orden:

    1. Definición.

    2. ¿Por qué es importante aprender este tema?

    3. Conceptos fundamentales.

    4. Explicación paso a paso.

    5. Ejemplo práctico.

    6. Buenas prácticas.

    7. Errores comunes.

    8. Resumen final.

    Escribe varios párrafos.

    No respondas con un único párrafo corto.

    No preguntes nada.

    No finalices diciendo que puedes ampliar el tema.

    La explicación debe ser completa antes de terminar.

    La respuesta debe ser extensa.

    Escribe entre 6 y 10 párrafos.

    No hagas resúmenes demasiado cortos.

    Desarrolla suficientemente cada sección antes de finalizar
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

    def _build_administrative_prompt(
        self,
        tracker: Tracker,
    ) -> str:
        """
        Construye el mensaje base para consultas
        administrativas.
        """

        latest = tracker.latest_message or {}

        return latest.get(
            "text",
            "",
        ).strip()
     
    
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

         macroflujo = request_context.get(
             "macroflujo",
             flow,
         )
  
         subflujo = request_context.get(
             "subflujo",
             request_context.get(
                "flujo",
                "",
             ),
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

             # --------------------------------------------------
             # Aprendizaje de un tema
             # Únicamente aquí tiene sentido detectar materia.
             # --------------------------------------------------

             if subflujo == "aprender_tema":
             
             
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
             
             # --------------------------------------------------
             # Resto de flujos académicos
             # (certificados, horarios, notas, pagos, tutor, etc.)
             # --------------------------------------------------

             else:

                 context.update(

                     {

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


         elif macroflujo in (

             "administrative",

             self.FLOW_ADMINISTRATIVE,

         ):

             context.update(

                 {

                     "programa": tracker.get_slot(
                         "programa"
                     ),

                     "ficha": tracker.get_slot(
                         "ficha"
                     ),

                     "estado": tracker.get_slot(
                         "estado_estudiante"
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

        logger.warning("=" * 80)
        logger.warning("[ACADEMICO] _build_topic_events")
        logger.warning("latest_message=%s", latest)
        logger.warning("tema capturado=%s", tema)
        logger.warning("tema_actual=%s", tracker.get_slot("tema_actual"))
        logger.warning("tema_consulta=%s", tracker.get_slot("tema_consulta"))
        logger.warning("esperando_tema=%s", tracker.get_slot("esperando_tema"))
        logger.warning("=" * 80)

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
                "nivel_explicacion",
                "basico",
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


    def _is_new_topic(
        self,
        tracker,
        texto,
    ):

        """
        Determina si el usuario cambió completamente de tema o si
        simplemente continúa realizando preguntas sobre el mismo.

        True  -> Nuevo tema.
        False -> Continuación / subconsulta.
        """

        tema_actual = (
            tracker.get_slot("tema_actual")
            or ""
        ).lower().strip()

        if not tema_actual:
            return True

        texto = texto.lower().strip()

        if "?" in texto:
            return False

        if texto.startswith((
            "que",
            "qué",
            "como",
            "cómo",
            "por qué",
            "porque",
            "cual",
            "cuál",
            "cuando",
            "cuándo",
            "donde",
            "dónde",
            "para qué",
            "para que",
        )):
            return False

        materia_actual = detectar_materia(
            tema_actual
        )

        materia_nueva = detectar_materia(
            texto
        )

        if (
            materia_actual
            and materia_nueva
            and materia_actual != materia_nueva
        ):
            logger.info(
                "[ACADEMICO] Cambio de materia detectado."
            )
            
            return True

        if tema_actual in texto:
      
            logger.info(
               "[ACADEMICO] El tema actual aparece dentro del texto."
            )
            return False
        # ----------------------------------------
        # Si alguna palabra importante coincide,
        # probablemente sigue hablando
        # del mismo tema.
        # ----------------------------------------

        palabras_actual = {
            p
            for p in tema_actual.split()
            if len(p) > 3
        }

        palabras_texto = {
            p
            for p in texto.split()
            if len(p) > 3
        }

        coincidencias = palabras_actual.intersection(
            palabras_texto
        )

        logger.info(
            "[ACADEMICO] Coincidencias=%s",
            coincidencias,
        )

        if coincidencias:
            logger.info(
                "[ACADEMICO] Se mantiene el mismo tema."
            )
            
            return False

        # ----------------------------------------
        # Frases muy cortas suelen ser
        # un nuevo tema.
        # ----------------------------------------

        if len(texto.split()) <= 2:
            
            logger.info(
                "[ACADEMICO] Cambio de tema: texto muy corto."
            )
            return True

       
        logger.info(
            "[ACADEMICO] Sin coincidencias relevantes. Se mantiene el tema actual."
        )

        return True

    def _build_continue_prompt(
        self,
        tracker: Tracker,
        nivel=None,
    ):
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

        if nivel is None:

            nivel = (
               tracker.get_slot(
                   "nivel_explicacion"
               )
               or "basico"
            )

        if nivel == "basico":

            instrucciones = """
        Continúa ampliando los conceptos básicos del tema.

        Mantén un lenguaje fácil de comprender.

        No profundices demasiado en aspectos técnicos.
        """

        elif nivel == "intermedio":

            instrucciones = """
        Ahora profundiza en el funcionamiento interno del mismo tema.

        Relaciona conceptos.

        Explica el funcionamiento interno.

        Incluye casos prácticos.

        Introduce terminología técnica cuando sea necesaria.
        """

        else:

            instrucciones = """
        Ahora desarrolla aspectos avanzados del mismo tema, incluyendo arquitectura, optimización y casos reales.

        Incluye arquitectura.

        Casos reales.

        Comparaciones técnicas.

        Errores frecuentes.

        Buenas prácticas profesionales.

        Optimización.

        Finaliza con un ejercicio práctico resuelto.
        """

        ultima_respuesta = (
            tracker.get_slot("ultima_respuesta_llm")
            or ""
        ).strip()
        if len(ultima_respuesta) > 1200:
            ultima_respuesta = ultima_respuesta[-1200:]
        prompt = f"""
        El estudiante está estudiando el mismo tema.

        Tema:

        {tema}

        Nivel actual:

        {nivel}

        Esta conversación NO corresponde a un tema nuevo.

        Corresponde a la continuación de una explicación previamente iniciada.

        Debes continuar exactamente desde donde terminó la explicación anterior.

        No reinicies el tema.

        No vuelvas a realizar una introducción.

        No vuelvas a definir conceptos que ya fueron explicados.

        No repitas ejemplos anteriores.

        Asume que el estudiante ya comprendió todo lo explicado hasta este momento.

        La primera oración debe comenzar como una continuación natural.

        Ejemplos:

        "Ahora que comprendemos los conceptos básicos..."

        "A continuación profundizaremos..."

        "Una vez entendida la estructura general..."

        Nunca empieces diciendo:

        "El modelo OSI es..."

        "Fundamentos de programación es..."

        "Variables son..."

        porque eso indica que reiniciaste la explicación.

        """

        if ultima_respuesta:

            prompt += f"""

        La explicación anterior fue exactamente la siguiente:

        ------------------------------------------------------------

        {ultima_respuesta}

         ------------------------------------------------------------

         La explicación mostrada arriba representa el contenido que el estudiante YA leyó.

         Considera toda esa información como conocida.

         Tu respuesta debe comenzar exactamente después del último concepto desarrollado.

         No repitas párrafos.

         No repitas listas.

         No repitas definiciones.

         No vuelvas al inicio del tema.


         """
        logger.info("=" * 70)
        logger.info("[LLM] Prompt CONTINUE")
        logger.info(prompt)
        logger.info("=" * 70)

        prompt += "\n\n"
        prompt += instrucciones
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
            logger.info(
                "esperando_tema=%s",
                tracker.get_slot("esperando_tema"),
            )
            logger.info("=" * 70)

            logger.info(
                "TIPO TRACKER=%s",
                type(tracker),
)
            
            nuevo_nivel = self._next_explanation_level(
                tracker
            )
            logger.info(
                "nuevo_nivel=%s",
                nuevo_nivel,
            )
            logger.info(
                "[ACADEMICO] Se enviará SlotSet(nivel_explicacion=%s)",
                nuevo_nivel,
            )

            prompt = self._build_continue_prompt(
                tracker,
                nivel=nuevo_nivel,
            )
            return (

                limpieza

                + [

                    SlotSet(
                        "continuando_tema",
                        True,
                    ),

                    SlotSet(
                        "nivel_explicacion",
                        nuevo_nivel,
                    ),
                    logger.info(
                        "[ACADEMICO] Guardando nivel_explicacion=%s",
                        nuevo_nivel,
                    )

                ]

                + self._ejecutar_procesamiento_llm(

                    dispatcher,
                    tracker,
                    self.FLOW_ACADEMIC,
                    prompt=prompt,

            )

)

        # ======================================================
        # MODO APRENDIZAJE
        #
        # El usuario ya tiene un tema activo.
        #
        # Puede:
        #   1. Cambiar completamente de tema.
        #   2. Hacer una subconsulta.
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

            texto = tracker.latest_message["text"].strip()

            tema_actual = (
                tracker.get_slot("tema_actual") or ""
            ).strip()


            # --------------------------------------------------
            # Decisión: ¿nuevo tema o continuación?
            # --------------------------------------------------

            es_nuevo = self._is_new_topic(
                tracker,
                texto,
            )

            logger.info(
                "[ACADEMICO] ¿Nuevo tema?: %s",
                es_nuevo,
            )

            # --------------------------------------------------
            # CAMBIO DE TEMA
            # --------------------------------------------------

            if es_nuevo:

                logger.info(
                    "[ACADEMICO] Nuevo tema detectado."
                )

                logger.info(
                    "[ACADEMICO] Reiniciando explicación | nuevo tema=%s",
                    texto,
                )

                return (
                    
                    limpieza

                    + [

                         SlotSet(
                             "tema_anterior",
                             tema_actual,
                         ),

                         SlotSet(
                             "cambio_tema",
                             True,
                         ),

                         SlotSet(
                             "tema_actual",
                             texto,
                         ),

                         SlotSet(
                             "tema_consulta",
                             texto,
                         ),

                         SlotSet(
                             "nivel_explicacion",
                             "basico",
                         ),

                         SlotSet(
                             "ultima_respuesta_llm",
                             None,
                         ),

                         SlotSet(
                             "continuando_tema",
                             False,
                         ),

                    ]
                    
                    + self._ejecutar_procesamiento_llm(

                        dispatcher,

                        tracker,

                        self.FLOW_ACADEMIC,

                    )

               )
            
            # --------------------------------------------------
            # SUBCONSULTA
            # --------------------------------------------------

            logger.info(
                "[ACADEMICO] Subconsulta detectada."
            )

            logger.info(
                "[ACADEMICO] Tema principal=%s | Subtema=%s",
                tema_actual,
                texto,
            )

            logger.info(
                "[ACADEMICO] Enviando al LLM | tema=%s | consulta=%s | continuando=%s",
                tracker.get_slot("tema_actual"),
                texto,
                True,
            )
            
            return (

                limpieza

                + [

                    SlotSet(
                        "tema_consulta",
                        texto,
                    ),
                    SlotSet(
                        "continuando_tema",
                        True,
                    ),

                    SlotSet(
                        "cambio_tema",
                        False,
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
        # Primera explicación.
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

            logger.warning("=" * 80)
            logger.warning("[ACADEMICO] ENTRANDO A _build_topic_events")
            logger.warning(
                "latest_message=%s",
                tracker.latest_message.get("text"),
            )
            logger.warning(
                "tema_actual=%s",
                tracker.get_slot("tema_actual"),
            )
            logger.warning(
                "tema_consulta=%s",
                tracker.get_slot("tema_consulta"),
            )
            logger.warning("=" * 80)
            return (

                limpieza

                + self._build_topic_events(
                    tracker,
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
        logger.info(
            "TRACKER RECIBIDO=%s",
            type(tracker),
        ) 
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
        "[LLM] nivel_explicacion recibido=%s",
        tracker.get_slot("nivel_explicacion"),
        )
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

               # =====================================================
               # Compatibilidad entre el formato antiguo ("flujo")
               # y el nuevo ("macroflujo").
               # =====================================================
                flujo_llm = (
                   context_llm.get("macroflujo")
                   or context_llm.get("flujo")
                )

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

                   logger.info(
                       "[LLM] macro=%s | sub=%s | next_action=%s | pending=%s",
                       context.get("macroflujo"),
                       context.get("subflujo"),
                       llm_request.get("next_action"),
                       context.get("pending_action"),
                   )

                fallback = llm_request.get(
                    "fallback",
                    "Lo siento, no puedo responder en este momento.",
                )

            # =====================================================
            # NO hay llm_request
            # (flujo académico clásico, continuar tema, etc.)
            # =====================================================

            else:

                if prompt is None:

                    prompt = self._build_prompt(
                        tracker,
                    )

                context = self._build_llm_context(
                    tracker,
                    flow,
                )

                logger.info(
                    "[LLM] flujo clásico | macro=%s | sub=%s",
                    context.get("macroflujo"),
                    context.get("subflujo"),
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
            logger.warning("=" * 80)
            logger.warning("PROMPT ACADÉMICO FINAL")
            logger.warning(prompt)
            logger.warning("=" * 80)


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

                events.extend(

                    [

                         SlotSet(
                             "continuando_tema",
                             False,
                         ),

                         SlotSet(
                             "cambio_tema",
                             False,
                         ),

                    ]

                )

            logger.info(
                "[LLM] nivel_explicacion al salir=%s",
                tracker.get_slot("nivel_explicacion"),
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