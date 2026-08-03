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
from .core.nlp_utils import build_llm_request
# ---------------------------------------------------------------------
# Configuración del módulo
# ---------------------------------------------------------------------

logger = logging.getLogger(__name__)

#: Número máximo de intentos permitidos durante formularios
#: (se mantiene por compatibilidad con el flujo existente).
MAX_INTENTOS_FORM: int = 3


def validar_respuesta(
    tracker,
    dispatcher,
    intents_validos,
    mensaje,
):
  
    intent = tracker.get_intent_of_latest_message()

    if intent not in intents_validos:
   
        return False
    dispatcher.utter_message(text=mensaje)

    return True

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

    
    
    FLOW_GENERAL = "general"
    FLOW_ACADEMIC = "academic"
    FLOW_SUPPORT = "support"
    FLOW_AUTH = "auth"
    FLOW_ADMINISTRATIVE = "administrative"
    FLOW_HELP = "help"

    # ==========================================
    # Compatibilidad con arquitectura anterior
    # ==========================================

    ACADEMIC_LEARNING_PROCESSES = {
        "aprender_tema",
    }
    
    ADMIN_PROCESSES = {
        "consultar_horarios",
        "consultar_progreso",
        "consultar_estado",
        "consultar_ficha",
        "consultar_historial",
        "consultar_inscripciones",
        "consultar_certificados",
        "consultar_pagos",
        "consultar_notas",
        "consultar_tutor",
}

    SPECIAL_MACROFLOWS = (
        "guardian_encuesta",
        "guardian_autenticacion",
        "guardian_recuperacion",
        "cierre_conversacion",
    )

    SUPPORT_PROCESSES = {
       "faq",
       "pqrsd",
       "crear_caso",
       "hablar_asesor",
       "contactar_tutor",
       "recuperar_contrasena",
    }
    
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

        flujo = request_context.get(
           "flujo"
        )

        if not macroflujo and flujo:

            logger.info(
                "[FLOW] Compatibilidad: promoviendo flujo '%s' como macroflujo.",
                flujo,
            )

            macroflujo = flujo

        logger.warning("=" * 80)
        logger.warning("LLM REQUEST RECIBIDO")
        logger.warning("%s", llm_request)
        logger.warning(
            "[FLOW] macro=%s sub=%s flujo=%s proceso=%s esperando=%s",
            macroflujo,
            subflujo,
            flujo,
            tracker.get_slot("proceso_activo"),
            tracker.get_slot("esperando_tema"),
        )
        logger.warning("=" * 80)
        
        
            
        # ======================================================
        # ESTADOS ESPECIALES PENDIENTES
        # TIENEN PRIORIDAD SOBRE MACROFLUJO GENERAL
        # ======================================================

        if tracker.get_slot("esperando_resolucion"):
    
            proceso = tracker.get_slot("proceso_activo")

            logger.info(
                "[FLOW] Resolución pendiente. Conservando proceso=%s",
                proceso,
            )

            if proceso in (
                "faq",
                "pqrsd",
            ):
                 return self.FLOW_SUPPORT


            if proceso == "aprender_tema":
                return self.FLOW_ACADEMIC


        if tracker.get_slot("esperando_decision_post_resolucion"):

            proceso = tracker.get_slot("proceso_activo")

            logger.info(
                "[FLOW] Decisión post resolución. proceso=%s",
                proceso,
            )

            if proceso in (
                "faq",
                "pqrsd",
            ):
                return self.FLOW_SUPPORT


            if proceso == "aprender_tema":
                return self.FLOW_ACADEMIC    
            
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

                proceso = tracker.get_slot("proceso_activo")
       
                logger.info(
                    "[FLOW] Support -> proceso=%s subflujo=%s",
                    proceso,
                    subflujo,
                )

                return self.FLOW_SUPPORT

            if macroflujo == "auth":
                return self.FLOW_AUTH

            if macroflujo == "help":
                return self.FLOW_HELP

            if macroflujo == "general":
                return self.FLOW_GENERAL

            if macroflujo == "administrative":

                logger.info(
                "[FLOW] Administrativo -> proceso=%s subflujo=%s",
                tracker.get_slot("proceso_activo"),
                subflujo,
            )

            return self.FLOW_ADMINISTRATIVE

            # ------------------------------------------
            # Macroflujos especiales
            # ------------------------------------------

            if macroflujo in self.SPECIAL_MACROFLOWS:

                 logger.info(
                     "[FLOW] Macroflujo especial=%s",
                     macroflujo,
                 )

                 return self.FLOW_GENERAL

            if macroflujo == "auth_required":
                 return self.FLOW_AUTH

        # ======================================================
        # COMPATIBILIDAD CON FLUJOS ANTIGUOS
        # ======================================================

        if flujo in self.SPECIAL_MACROFLOWS:

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

        if tracker.get_slot("confirmacion_cierre") == "pendiente":
            return self.FLOW_GENERAL

        
        # ======================================================
        # COMPATIBILIDAD CON LA ARQUITECTURA ANTERIOR
        # Se utiliza únicamente cuando el ACTION_CATALOG aún
        # no ha definido el macroflujo.
        # ======================================================

        proceso = tracker.get_slot("proceso_activo")

        tema = tracker.get_slot("tema_consulta")

        materia = tracker.get_slot("materia_detectada")

        esperando = tracker.get_slot(
            "esperando_tema"
        )

        logger.debug(
            "[FLOW] proceso=%s pending=%s tema=%s materia=%s",
            proceso,
            tracker.get_slot("pending_action"),
            bool(tema),
            bool(materia),
        )

        # -----------------------------------------------------
        # SOPORTE
        # -----------------------------------------------------

        if proceso in self.SUPPORT_PROCESSES:

            logger.info(
                "[FLOW] Flujo soporte detectado. proceso=%s",
                proceso,
            )

            return self.FLOW_SUPPORT

        # -----------------------------------------------------
        # ADMINISTRATIVO
        # -----------------------------------------------------

        if proceso in self.ADMIN_PROCESSES:

            logger.info(
                "[FLOW] Flujo administrativo detectado. proceso=%s",
                proceso,
            )

            return self.FLOW_ADMINISTRATIVE

        # -----------------------------------------------------
        # APRENDER TEMA
        # -----------------------------------------------------

        if proceso in self.ACADEMIC_LEARNING_PROCESSES:

            logger.info(
                "[FLOW] Flujo aprendizaje detectado. proceso=%s",
                proceso,
            )

            return self.FLOW_ACADEMIC


        # -----------------------------------------------------
        # COMPATIBILIDAD CON FLUJOS ANTIGUOS
        # -----------------------------------------------------

        if esperando:

            return self.FLOW_ACADEMIC

        if proceso in self.ACADEMIC_LEARNING_PROCESSES:

            return self.FLOW_ACADEMIC

        # ======================================================
        # AYUDA
        # ======================================================

        if intent == "ayuda":
            return self.FLOW_HELP

        # ======================================================
        # GENERAL
        # ======================================================
        logger.warning(
            "[FLOW DEBUG] Sin macroflujo detectado"
        )   

        logger.warning(
            "[FLOW DEBUG] intent=%s proceso=%s esperando_tema=%s",
            intent,
            proceso,
            tracker.get_slot("esperando_tema"),
        )
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

        logger.warning(
            "[ACADEMICO PROMPT] tema_actual=%s tema_consulta=%s latest=%s",
            tracker.get_slot("tema_actual"),
            tracker.get_slot("tema_consulta"),
            latest.get("text"),
        )
        
        texto = latest.get("text", "").strip()

        if texto.startswith("/"):
            texto = ""

        pregunta = (
            tracker.get_slot("tema_consulta")
            or texto
        )

        tema_principal = (
            tracker.get_slot("tema_actual")
            or pregunta
        )

        if not tema_principal:

            logger.error(
                "[ACADEMICO] Tema principal vacío."
            )

            return (
                "El usuario desea aprender un tema, "
                "pero aún no ha indicado cuál."
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
        nivel_explicacion: str | None = None,
        tema_actual=None,
        tema_consulta=None,
     ) -> Dict[str, Any]:
         """
         Construye el contexto estructurado enviado al Prompt Builder.

         El contexto depende del macroflujo.

         No todos los flujos requieren información académica.

         Mantiene compatibilidad con la arquitectura actual.
         """

         tema_actual_ctx = (
             tema_actual
             if tema_actual is not None
             else tracker.get_slot("tema_actual")
         )

         tema_consulta_ctx = (
             tema_consulta
             if tema_consulta is not None
             else tracker.get_slot("tema_consulta")
         )

         nivel_ctx = (
             nivel_explicacion
             if nivel_explicacion is not None
             else tracker.get_slot("nivel_explicacion")
         )
         
         
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

         if macroflujo in ("general", self.FLOW_GENERAL):

             proceso = tracker.get_slot("proceso_activo")

             logger.info(
                 "[LLM CONTEXT] Reconstruyendo macroflujo desde proceso=%s",
                 proceso,
             )
 
             if proceso in self.ACADEMIC_LEARNING_PROCESSES:
                 macroflujo = "academic"
                 subflujo = proceso

             elif proceso in self.SUPPORT_PROCESSES:
                 macroflujo = "support"
                 subflujo = proceso

             elif proceso in self.ADMIN_PROCESSES:
                 macroflujo = "administrative"
                 subflujo = proceso

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
                     tema_consulta_ctx
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

                         "tema_actual": tema_actual_ctx,

                         "tema_consulta": tema_consulta_ctx,

                         "nivel_explicacion": nivel_ctx,

                     }

                 )
             
             # --------------------------------------------------
             # Resto de flujos académicos
             # (certificados, horarios, notas, pagos, tutor, etc.)
             # --------------------------------------------------

             else:

                 context.update(

                     {

                         "tema_actual": tema_actual_ctx,

                         "tema_consulta": tema_consulta_ctx,

                         "nivel_explicacion": nivel_ctx,

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
    # CONTEXTO ADMINISTRATIVO
    # ======================================================
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
             "[LLM CONTEXT] macro=%s | sub=%s | tema=%s | nivel=%s",
             macroflujo,
             subflujo,
             tema_actual_ctx,
             nivel_ctx,
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
        tracker: Tracker,
    ) -> List[EventType]:
        """
        Construye únicamente eventos definidos explícitamente
        por llm_request.

        La lógica de continuidad por macroflujo se maneja en:
            _postprocess_academic()
            _postprocess_support()
            _postprocess_administrative()

        Evita duplicar FollowupAction.
        """

        logger.warning(
            "[FOLLOWUP] flow=%s",
            flow,
        )

        llm_request = tracker.get_slot(
            "llm_request"
        ) or {}

        next_action = llm_request.get(
            "next_action"
        )

        # ======================================================
        # PRIORIDAD 1
        # El orquestador definió la siguiente acción
        # ======================================================

        if next_action:

            logger.info(
                "[FOLLOWUP] usando next_action=%s",
                next_action,
            )

            return [

                FollowupAction(
                    next_action,
                ),

            ]

        # ======================================================
        # FALLBACK
        # Reconstrucción cuando llm_request ya fue limpiado
        # ======================================================

        proceso = tracker.get_slot(
            "proceso_activo"
        )

        logger.info(
            "[FOLLOWUP] Reconstruyendo desde proceso=%s",
            proceso,
        )

        if proceso == "aprender_tema":

            return [

                FollowupAction(
                    "action_ofrecer_continuar_tema",
                ),

            ]

        if proceso == "faq":

            return [

                FollowupAction(
                    "action_ofrecer_continuar_faq",
                ),

            ]

        if proceso == "pqrsd":

            return [

                FollowupAction(
                    "action_ofrecer_radicar_pqrsd",
                ),

            ]
        if proceso in {

             "crear_caso",
             "hablar_asesor",
             "contactar_tutor",
             "recuperar_contrasena",

        }:

             return [

                 FollowupAction(
                     "action_ofrecer_continuar_soporte",
                 ),

             ]
        # ------------------------------------------------------
        # ADMINISTRATIVO
        # ------------------------------------------------------

        if proceso in {

            "consultar_estado",
            "consultar_tutor",
            "consultar_horarios",
            "consultar_progreso",
            "consultar_historial",
            "consultar_certificados",
            "consultar_pagos",
            "consultar_notas",
            "consultar_ficha",
            "consultar_inscripciones",

        }:

            return [

                FollowupAction(
                    "action_ofrecer_continuar_administrativo",
                ),

            ]

        # ======================================================
        # Sin continuidad
        # ======================================================

        return []
    
    # ==========================================================
    # ROUTER POSTPROCESAMIENTO POR MACROFLUJO
    # ==========================================================

    def _postprocess_flow(
        self,
        flow: str,
        tracker: Tracker,
        respuesta: str,
        llm_request: dict,
    ) -> List[EventType]:
        """
        Distribuye el postprocesamiento según macroflujo.

        Cada flujo conserva su propia lógica sin mezclar
        responsabilidades.
        """

        if flow == self.FLOW_ACADEMIC:

            return self._postprocess_academic(
                tracker,
                respuesta,
                llm_request,
            )


        if flow == self.FLOW_SUPPORT:

            return self._postprocess_support(
                tracker,
                respuesta,
                llm_request,
            )


        if flow == self.FLOW_ADMINISTRATIVE:

            return self._postprocess_administrative(
                tracker,
                respuesta,
                llm_request,
        )


        return []
    
    
    # POSTPROCESAMIENTO ACADÉMICO
    # ==========================================================

    def _postprocess_academic(
        self,
        tracker: Tracker,
        respuesta: str,
        llm_request: dict,
    ) -> List[EventType]:

        events = [

            SlotSet(
                "ultima_respuesta_llm",
                respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),

            SlotSet(
                "continuando_tema",
                False,
            ),

            SlotSet(
                "cambio_tema",
                False,
            ),

        ]

        proceso = tracker.get_slot(
            "proceso_activo"
        )

        logger.info(
            "[POSTPROCESS] proceso=%s",
            proceso,
        )

        # ======================================================
        # Solo Aprender Tema continúa con profundización
        # ======================================================

        if proceso == "aprender_tema":

            events.append(

                FollowupAction(
                    "action_ofrecer_continuar_tema"
                )

            )

        return events


    def _postprocess_support(
        self,
        tracker: Tracker,
        respuesta: str,
        llm_request: dict,
    ) -> List[EventType]:
        """
        Router del macroflujo de soporte.

        No realiza procesamiento.
        Solo delega según el subflujo.
        """

        proceso = tracker.get_slot(
            "proceso_activo"
        )

        if proceso == "faq":

            return self._postprocess_support_faq(
                tracker,
                respuesta,
                llm_request,
            )

        if proceso == "pqrsd":

            return self._postprocess_support_pqrsd(
                tracker,
                respuesta,
                llm_request,
            )

        if proceso == "crear_caso":
            return self._postprocess_support_crear_caso(
                tracker,
                respuesta,
                llm_request,
            )

        if proceso == "hablar_asesor":
            return self._postprocess_support_hablar_asesor(
                tracker,
                respuesta,
                llm_request,
            )

        if proceso == "contactar_tutor":
            return self._postprocess_support_contactar_tutor(
                tracker,
                respuesta,
               llm_request,
            )
        if proceso == "recuperar_contrasena":
            return self._postprocess_support_contactar_tutor(
                tracker,
                respuesta,
               llm_request,
            )        
        
        return []


    
    def _postprocess_support_faq(
        self,
        tracker: Tracker,
        respuesta: str,
        llm_request: dict,
    ) -> List[EventType]:

        logger.info(
            "[POSTPROCESS] FAQ continuidad"
        )
        events = [

            SlotSet(
                "ultima_respuesta_llm",
                respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),

            SlotSet(
                "esperando_pregunta_faq",
                False,
            ),

        ]

        return events

    def _postprocess_support_pqrsd(
        self,
        tracker: Tracker,
        respuesta: str,
        llm_request: dict,
    ) -> List[EventType]:

        logger.info(
            "[POSTPROCESS] PQRSD iniciar radicación"
        )

        events = [

            SlotSet(
                "ultima_respuesta_llm",
                 respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),

            SlotSet(
                "esperando_pqrsd",
                False,
            ),

        ]

        return events

    def _postprocess_support_crear_caso(
        self,
        tracker: Tracker,
        respuesta: str,
        llm_request: dict,
    ) -> List[EventType]:

        logger.info(
            "[POSTPROCESS] Crear caso"
        )

        events = [

            SlotSet(
                "ultima_respuesta_llm",
                 respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),
            SlotSet(
                "proceso_activo",
                "crear_caso",
            ),

        ]

        return events



    def _postprocess_support_hablar_asesor(
        self,
        tracker: Tracker,
        respuesta: str,
        llm_request: dict,
    ) -> List[EventType]:

        logger.info(
            "[POSTPROCESS] Hablar asesor"
        )

        events = [

            SlotSet(
                "ultima_respuesta_llm",
                 respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),
            SlotSet(
                "proceso_activo",
                "hablar_asesor",
            ),

        ]

        return events


    def _postprocess_support_contactar_tutor(
        self,
        tracker: Tracker,
        respuesta: str,
        llm_request: dict,
    ) -> List[EventType]:

        logger.info(
            "[POSTPROCESS] Contactar tutor"
        )

        events = [

            SlotSet(
                "ultima_respuesta_llm",
                 respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),
            SlotSet(
                "proceso_activo",
                "contactar_tutor",
            ),

        ]

        return events

    def _postprocess_support_recuperar_contrasena(
        self,
        tracker: Tracker,
        respuesta: str,
        llm_request: dict,
    ) -> List[EventType]:

        logger.info(
            "[POSTPROCESS] Recuperar contraseña"
        )

        events = [

            SlotSet(
                "ultima_respuesta_llm",
                 respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),

            SlotSet(
                "proceso_activo",
                "recuperar_contrasena",
            ),
        ]

        return events


    def _postprocess_administrative(
        self,
        tracker,
        respuesta,
        llm_request,
    ):

        proceso = tracker.get_slot("proceso_activo")

        if proceso == "consultar_estado":
            return self._postprocess_admin_estado(
                tracker,
                respuesta,
                llm_request,
            )

        if proceso == "consultar_certificados":
            return self._postprocess_admin_certificados(
                tracker,
                respuesta,
                llm_request,
            )

        if proceso == "consultar_tutor":
            return self._postprocess_admin_tutor(
                tracker,
                respuesta,
                llm_request,
            )

        if proceso == "consultar_horarios":
            return self._postprocess_admin_horarios(
                tracker,
                respuesta,
                llm_request,
            )

        if proceso == "consultar_historial":
            return self._postprocess_admin_historial(
                tracker,
                respuesta,
                llm_request,
            )

        if proceso == "consultar_progreso":
            return self._postprocess_admin_progreso(
                tracker,
                respuesta,
                llm_request,
            )

        if proceso == "consultar_pagos":
            return self._postprocess_admin_pagos(
                tracker,
                respuesta,
                llm_request,
            )

        if proceso == "consultar_notas":
            return self._postprocess_admin_notas(
                tracker,
                respuesta,
                llm_request,
            )

        if proceso == "consultar_ficha":
            return self._postprocess_admin_ficha(
                tracker,
                respuesta,
                llm_request,
            )

        if proceso == "consultar_inscripciones":
            return self._postprocess_admin_inscripciones(
                tracker,
                respuesta,
                llm_request,
            )

        return []


    def _postprocess_admin_consultar_estado(
        self,
        tracker,
        respuesta,
        llm_request,
    ):

        return [

            SlotSet(
                "ultima_respuesta_llm",
                respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),
            SlotSet(
                "proceso_activo",
                "consultar_estado",
            ),

        ]

    def _postprocess_admin_consultar_certificados(
        self,
        tracker,
        respuesta,
        llm_request,
    ):

        return [

            SlotSet(
                "ultima_respuesta_llm",
                respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),
            SlotSet(
                "proceso_activo",
                "consultar_certificados",
            ),


        ]

    def _postprocess_admin_consultar_tutor(
        self,
        tracker,
        respuesta,
        llm_request,
    ):

        return [

            SlotSet(
                "ultima_respuesta_llm",
                respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),
            SlotSet(
                "proceso_activo",
                "consultar_tutor",
            ),

        ]


    def _postprocess_admin_consultar_horarios(
        self,
        tracker,
        respuesta,
        llm_request,
    ):

        return [

            SlotSet(
                "ultima_respuesta_llm",
                respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),
            SlotSet(
                "proceso_activo",
                "consultar_horarios",
            ),

        ]
    def _postprocess_admin_consultar_historial(
        self,
        tracker,
        respuesta,
        llm_request,
    ):

        return [

            SlotSet(
                "ultima_respuesta_llm",
                respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),
            SlotSet(
                "proceso_activo",
                "consultar_historial",
            ),

        ]

    def _postprocess_admin_consultar_progreso(
        self,
        tracker,
        respuesta,
        llm_request,
    ):

        return [

            SlotSet(
                "ultima_respuesta_llm",
                respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),
            SlotSet(
                "proceso_activo",
                "consultar_progreso",
            ),

        ]

    def _postprocess_admin_admin_consultar_pagos(
        self,
        tracker,
        respuesta,
        llm_request,
    ):

        return [

            SlotSet(
                "ultima_respuesta_llm",
                respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),
            SlotSet(
                "proceso_activo",
                "consultar_pagos",
            ),

        ]

    def _postprocess_admin_consultar_notas(
        self,
        tracker,
        respuesta,
        llm_request,
    ):

        return [

            SlotSet(
                "ultima_respuesta_llm",
                respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),
            SlotSet(
                "proceso_activo",
                "consultar_notas",
            ),

        ]

    def _postprocess_admin_consultar_ficha(
        self,
        tracker,
        respuesta,
        llm_request,
    ):

        return [

            SlotSet(
                "ultima_respuesta_llm",
                respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),
            SlotSet(
                "proceso_activo",
                "consultar_ficha",
            ),

        ]


    def _postprocess_admin_consultar_inscripciones(
        self,
        tracker,
        respuesta,
        llm_request,
    ):

        return [

            SlotSet(
                "ultima_respuesta_llm",
                respuesta,
            ),

            SlotSet(
                "ultima_interaccion",
                datetime.utcnow().isoformat(),
            ),
            SlotSet(
                "proceso_activo",
                "consultar_inscripciones",
            ),

        ]


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
    
    def _is_waiting_for_support(self, tracker: Tracker) -> bool:
        """
        Indica si el flujo de soporte está esperando la primera
        consulta del usuario.
        """

        return bool(
           tracker.get_slot("esperando_pregunta_faq")
           or tracker.get_slot("esperando_pqrsd")
        )




    def _build_topic_events(
        self,
        tracker: Tracker,
        proceso: str = "aprender_tema",
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
        eventos = []

        eventos.extend(

            [

                SlotSet(
                    "esperando_tema", False),
                
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
                   proceso,
                ),

            ]

        )

        if proceso == "aprender_tema":

             eventos.extend([

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

             ])

        return eventos

    def _build_topic_events_support(
        self,
        tracker: Tracker,
        proceso: str,
    ) -> List[EventType]:

        latest = tracker.latest_message or {}

        tema = (
            latest.get("text", "")
            .strip()
        )

        logger.warning("=" * 80)
        logger.warning("[SUPPORT] _build_topic_events_support")
        logger.warning("mensaje=%s", tema)
        logger.warning("proceso=%s", proceso)
        logger.warning("=" * 80)

        logger.info(
            "[SUPPORT] Inicializando flujo soporte."
        )

        eventos = [

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
                proceso,
            ),

        ]

        if proceso == "faq":

            eventos.insert(
                0,
                SlotSet(
                    "esperando_pregunta_faq",
                    False,
                ),
            )

        elif proceso == "pqrsd":

            eventos.insert(
                0,
                SlotSet(
                    "esperando_pqrsd",
                    False,
                ),
            )
        logger.warning(
            "[SUPPORT] Eventos de transición=%s",
             eventos,
        )
        return eventos
    
    def _build_topic_events_administrative(
        self,
        tracker: Tracker,
        proceso: str,
    ) -> List[EventType]:

        logger.info(
            "[ADMIN] Inicializando flujo administrativo."
        )

        logger.warning("=" * 80)
        logger.warning("[ADMIN] _build_topic_events_administrative")
        logger.warning("mensaje=%s", tema)
        logger.warning("proceso=%s", proceso)
        logger.warning("=" * 80)
        
        latest = tracker.latest_message or {}

        tema = latest.get(
            "text",
            "",
        ).strip()

        return [

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
                proceso,
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
            "[ACADEMICO] Sin coincidencias relevantes. Nuevo tema detectado."
        )

        return True

    def _build_continue_prompt(
        self,
        tracker: Tracker,
        nivel=None,
        modo="continuacion",
        tema=None,
    ) -> str:
        """
        Construye un prompt enriquecido para continuar una explicación ya
        iniciada aprovechando el contexto de la última respuesta generada
        por el LLM.
        """

        logger.info("=" * 70)
        logger.info("[LLM] USANDO _build_continue_prompt()")
        logger.info("tema_actual=%s", tracker.get_slot("tema_actual"))
        logger.info("tema_consulta=%s", tracker.get_slot("tema_consulta"))
        logger.info("nivel=%s", tracker.get_slot("nivel_explicacion"))
        logger.info(
            "ultima_respuesta=%s",
           bool(tracker.get_slot("ultima_respuesta_llm")),
        )
        logger.info("=" * 70)

        latest = tracker.latest_message or {}

        tema = (
            tema
            or tracker.get_slot("tema_actual")
            or tracker.get_slot("tema_consulta")
            or latest.get("text", "")
            or "el tema anterior"
        )

        consulta_actual = (
            tracker.get_slot("tema_consulta")
            or latest.get("text", "")
            or tema
        )

        if nivel is None:
            nivel = (
                tracker.get_slot("nivel_explicacion")
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

    # =====================================================
    # CONTEXTO PEDAGÓGICO
    # =====================================================

        if modo == "tema_nuevo":

            prompt = f"""
Tipo de aprendizaje:

Tema nuevo

Tema:

{tema}

Nivel inicial:

{nivel}

El estudiante acaba de iniciar este tema.

Comienza desde cero.

Haz una introducción clara.

Explica primero los conceptos fundamentales.

No asumas conocimientos previos.

Organiza la explicación de forma progresiva.

Al finalizar deja abierta la posibilidad de continuar aprendiendo.
"""

        elif modo == "subconsulta":

            prompt = f"""
Tipo de aprendizaje:

Subconsulta

Tema principal:

{tema}

Consulta realizada por el estudiante:

{consulta_actual}

Nivel actual:

{nivel}

La pregunta pertenece al mismo tema.

No es un tema nuevo.

Responde primero únicamente la duda realizada.

Utiliza la explicación anterior únicamente como contexto.

No vuelvas a explicar todo el tema.

Después de responder la duda, retoma naturalmente el hilo del aprendizaje.

No cambies de tema.

No reinicies la explicación.
"""

        else:

            prompt = f"""
Tipo de aprendizaje:

Continuación

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

        if modo != "tema_nuevo" and ultima_respuesta:

           prompt += f"""

La explicación anterior fue:

----------------------------

{ultima_respuesta}

----------------------------

Toda esa información ya fue aprendida.

No la repitas.

No reinicies el tema.

Comienza exactamente desde el último concepto desarrollado.

La continuidad debe seguir estas reglas:

1. Comienza con una transición muy breve (máximo dos frases) conectando la explicación anterior con la nueva.

2. Resume únicamente la idea principal de lo ya aprendido, sin repetir listas ni volver a explicar conceptos.

3. Introduce únicamente contenido nuevo.

4. Aumenta el nivel de profundidad respecto a la respuesta anterior.

5. Si el tema tiene varias partes, continúa con la siguiente parte lógica, nunca regreses al inicio.

6. Mantén continuidad como si fuera el siguiente capítulo del mismo libro.

7. Evita reutilizar párrafos completos de la respuesta anterior.

8. Solo vuelve a mencionar conceptos anteriores cuando sean necesarios para comprender el nuevo contenido.

9. Al finalizar deja abierta naturalmente la explicación para que pueda existir otro nivel de profundización.
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

        proceso = tracker.get_slot("proceso_activo")
        macro = context.get("macroflujo")
        sub = context.get("subflujo")

        logger.warning("=" * 80)
        logger.warning("[LLM] INVOCANDO MOTOR")
        logger.warning("flow=%s", flow)
        logger.warning("macroflujo=%s", macro)
        logger.warning("subflujo=%s", sub)
        logger.warning("proceso_activo=%s", proceso)
        logger.warning("tema_actual=%s", tracker.get_slot("tema_actual"))
        logger.warning("tema_consulta=%s", tracker.get_slot("tema_consulta"))
        logger.warning("prompt_chars=%s", len(prompt))
        logger.warning("=" * 80)

        # ------------------------------------------------------
        # Auditoría de coherencia de flujo (NO bloquea)
        # ------------------------------------------------------

        FLOW_MAP = {
            "faq": ("support", "faq"),
            "pqrsd": ("support", "pqrsd"),
            "aprender_tema": ("academic", "aprender_tema"),
        }

        esperado = FLOW_MAP.get(proceso)

        if esperado and esperado != (macro, sub):
            logger.warning(
                "[FLOW WARNING] proceso_activo=%s "
                "esperado=(%s,%s) "
                "recibido=(%s,%s)",
                proceso,
                esperado[0],
                esperado[1],
                macro,
                sub,
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

        respuesta = run_llm(
            prompt=prompt,
            tracker=tracker,
            context=context,
            fallback=fallback,
            dispatcher=dispatcher,
        )

        logger.warning("=" * 80)
        logger.warning("[LLM] RESPUESTA RECIBIDA")
        logger.warning(
            "respuesta_vacia=%s",
            not bool((respuesta or "").strip()),
        )
        logger.warning(
            "respuesta_chars=%s",
            len(respuesta or ""),
        )
        logger.warning("=" * 80)

        return respuesta


    def run(
        self,
        dispatcher,
        tracker,
        domain,
    ) -> List[EventType]:
        
        llm_request = tracker.get_slot("llm_request")

        logger.warning("=" * 80)
        logger.warning("LLM REQUEST RECIBIDO")
        logger.warning("%s", llm_request)
        logger.warning("=" * 80)
        
        logger.warning("=" * 80)
        logger.warning("[TRACE ENTRY ACTION_HANDLE]")
        logger.warning(
            "intent=%s",
            tracker.get_intent_of_latest_message()
        )
        logger.warning(
            "text=%s",
            tracker.latest_message.get("text")
        )
        logger.warning(
            "latest_message=%s",
            tracker.latest_message
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request")
        )
        logger.warning("=" * 80)
      
        logger.warning("=" * 80)
        logger.warning("[LLM] ENTRANDO A ACTION_HANDLE_WITH_LLM")
        logger.warning("sender=%s", tracker.sender_id)
        logger.warning("pending_action=%s", tracker.get_slot("pending_action"))
        logger.warning("proceso_activo=%s", tracker.get_slot("proceso_activo"))
        logger.warning("llm_request=%s", tracker.get_slot("llm_request"))
        logger.warning("requires_auth=%s", tracker.get_slot("requires_auth"))
        logger.warning("=" * 80)

        logger.warning("=" * 80)
        logger.warning("[HISTORIAL SLOT FAQ]")

        for e in tracker.events:
            if (
                e.get("event") == "slot"
                and e.get("name") == "esperando_pregunta_faq"
            ):
                 logger.warning("%s", e)

        logger.warning("=" * 80)
        
        logger.warning("=" * 80)
        logger.warning("[ENTRY ACTION_HANDLE_WITH_LLM]")
        logger.warning(
            "intent=%s",
            (tracker.latest_message.get("intent") or {}).get("name"),
        )
        logger.warning("text=%s", tracker.latest_message.get("text"))
        logger.warning(
            "esperando_resolucion=%s",
            tracker.get_slot("esperando_resolucion"),
        )
        logger.warning(
            "esperando_encuesta_general=%s",
            tracker.get_slot("esperando_encuesta_general"),
        )
        logger.warning(
            "confirmacion_cierre=%s",
            tracker.get_slot("confirmacion_cierre"),
        )
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning("=" * 80)

        logger.warning("=" * 80)
        logger.warning("[TRACKER] Eventos=%d", len(tracker.events))
        logger.warning("[TRACKER] Sender=%s", tracker.sender_id)
        logger.warning("=" * 80)

        logger.info("=" * 80)
        logger.info("[DEBUG ACTION_HANDLE_WITH_LLM]")
        logger.info(
            "intent=%s",
            tracker.get_intent_of_latest_message(),
        )
        logger.info(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.info(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.info(
            "tema_consulta=%s",
            tracker.get_slot("tema_consulta"),
        )
        logger.info(
            "materia_detectada=%s",
            tracker.get_slot("materia_detectada"),
        )
        logger.info("=" * 80)

        logger.warning("=========== SLOTS ===========")
        
        
        for k, v in tracker.current_slot_values().items():
           logger.warning("%s = %s", k, v)
        logger.warning("=============================")

        logger.warning("=" * 80)
        logger.warning("ÚLTIMOS 20 EVENTOS DEL TRACKER")
        for i, e in enumerate(tracker.events[-20:], 1):
            logger.warning("[%02d] %s", i, e)
        logger.warning("=" * 80)

        limpieza = [
            ActiveLoop(None),
            SlotSet("requested_slot", None),
        ]

        logger.warning(
            "[TRACE][ActionHandleWithLLM] llm_request=%s",
            tracker.get_slot("llm_request"),
        )

        logger.info(
            "[VALIDATION] cierre=%s resolucion=%s post=%s intent=%s",
            tracker.get_slot("confirmacion_cierre"),
            tracker.get_slot("esperando_resolucion"),
            tracker.get_slot("esperando_decision_post_resolucion"),
            tracker.get_intent_of_latest_message(),
        )

        # ======================================================
        # CONTEXTO DEL MENSAJE ACTUAL
        # ======================================================

        flow = self._detect_flow(tracker)
        intent = tracker.get_intent_of_latest_message()

        logger.warning("=" * 80)
        logger.warning("[FLOW DETECTADO]")
        logger.warning("flow=%s", flow)
        logger.warning("intent=%s", intent)
        logger.warning("proceso=%s", tracker.get_slot("proceso_activo"))
        logger.warning("llm_request=%s", tracker.get_slot("llm_request"))
        logger.warning("=" * 80)
        
        

        logger.info("[DEBUG] Flow detectado=%s", flow)
        logger.info("[DEBUG] Intent detectado=%s", intent)

        # ======================================================
        # VALIDACIÓN DECISIÓN POST RESOLUCIÓN
        # ======================================================

        if tracker.get_slot("esperando_decision_post_resolucion"):

            logger.info(
                "[POST_RESOLUCION] Intent=%s",
                intent,
            )

            if intent == "nlu_fallback":

                dispatcher.utter_message(
                    text=(
                        "Puedes seleccionar una opción del menú o escribir nuevamente tu consulta.:\n"
                        "• Continuar tema\n"
                        "• Menú principal\n"
                        "• Finalizar conversación\n\n"
                        "O escribir directamente una pregunta "
                        "relacionada con el tema actual."
                    )
                )

                return limpieza

        # ======================================================
        # VALIDACIÓN CIERRE
        # ======================================================

        if tracker.get_slot("confirmacion_cierre") == "pendiente":

            if validar_respuesta(
                tracker,
                dispatcher,
                ["affirm", "deny"],
                "No entendí tu respuesta. Por favor responde únicamente 'Sí' o 'No'.",
            ):
                return limpieza

        # ======================================================
        # VALIDACIÓN RESOLUCIÓN
        # ======================================================

        if tracker.get_slot("esperando_resolucion"):

            if validar_respuesta(
                tracker,
                dispatcher,
                [
                    "respuesta_resuelto_si",
                    "respuesta_resuelto_no",
                    "affirm",
                    "deny",
                ],
                "No entendí. ¿Tu problema quedó resuelto? Responde únicamente Sí o No.",
            ):
                return limpieza

        # ======================================================
        # ORQUESTADOR DE MACROFLUJOS
        # ======================================================

        if flow == self.FLOW_ACADEMIC:

            return self._run_academic(
                dispatcher,
                tracker,
                domain,
                limpieza,
            )

        if flow == self.FLOW_SUPPORT:

            return self._run_support(
                dispatcher,
                tracker,
                domain,
                limpieza,
            )

        if flow == self.FLOW_ADMINISTRATIVE:

            return self._run_administrative(
                dispatcher,
                tracker,
                domain,
                limpieza,
            )

        # ======================================================
        # FALLBACK
        # ======================================================

        return (

            limpieza

            + self._ejecutar_procesamiento_llm(

                dispatcher,

                tracker,

                flow,

            )

        )

    
    def _run_support(
        self,
        dispatcher,
        tracker,
        domain,
        limpieza,
    ) -> List[EventType]:

        intent = tracker.get_intent_of_latest_message()

        logger.info("=" * 70)
        logger.info("[SOPORTE] ENTRANDO A _run_support")
        logger.info(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.info(
            "intent=%s",
            intent,
        )
        logger.info("=" * 70)

        proceso = tracker.get_slot("proceso_activo")

        logger.info(
            "[SUPPORT] tema_actual=%s",
            tracker.get_slot("tema_actual"),
        )

        logger.info(
            "[SUPPORT] tema_consulta=%s",
            tracker.get_slot("tema_consulta"),
        )

        # ======================================================
        # ESPERANDO PRIMERA CONSULTA DE SOPORTE
        # FAQ o PQRSD
        # ======================================================

        if (
            proceso in ("faq", "pqrsd")
            and self._is_waiting_for_support(tracker)
        ):

            nuevo_tema = (
                 tracker.latest_message.get("text", "")
                .strip()
            )

            logger.info(
                "[TRANSICION %s] Primera consulta recibida: %s",
                proceso,
                nuevo_tema,
            )

            eventos = self._build_topic_events_support(
                tracker,
                proceso,
            )

            return (

                limpieza

                + eventos

                + self._ejecutar_procesamiento_llm(

                     dispatcher,

                     tracker,

                     self.FLOW_SUPPORT,

                     prompt=None,

                     tema_actual=nuevo_tema,

                     tema_consulta=nuevo_tema,

                )

            )
        
 
        # ======================================================
        # CONTINUAR FAQ
        # ======================================================

        if proceso == "faq" and intent == "continuar_faq":

            logger.info(
                "[SUPPORT] Continuando FAQ"
            )

            return (

                limpieza

                + self._ejecutar_procesamiento_llm(

                    dispatcher,

                    tracker,

                    self.FLOW_SUPPORT,

                    prompt=None,

                    tema_actual=tracker.get_slot(
                        "tema_actual"
                    ),

                    tema_consulta=tracker.get_slot(
                        "tema_consulta"
                    ),

                )

            )


        # ======================================================
        # PRIMERA DESCRIPCIÓN PQRSD
        # ======================================================

        if (
            proceso == "pqrsd"
            and tracker.get_slot("esperando_pqrsd")
        ):

            nuevo_tema = (
                tracker.latest_message.get("text", "")
               .strip()
            )

            logger.info(
                "[TRANSICION PQRSD] Primera descripción recibida=%s",
                nuevo_tema,
            )

            eventos = self._build_topic_events_support(
                tracker,
                proceso,
            )

            return (

                limpieza

                + eventos

                + self._ejecutar_procesamiento_llm(

                    dispatcher,

                    tracker,

                    self.FLOW_SUPPORT,

                    prompt=None,

                    tema_actual=nuevo_tema,

                    tema_consulta=nuevo_tema,

                )

            )

        # ======================================================
        # FLUJO NORMAL SOPORTE
        # ======================================================

        return (

            limpieza

            + self._ejecutar_procesamiento_llm(

                dispatcher,

                tracker,

                self.FLOW_SUPPORT,

            )

        )
    
    def _run_administrative(
        self,
        dispatcher,
        tracker,
        domain,
        limpieza,
    ) -> List[EventType]:

        intent = tracker.get_intent_of_latest_message()

        logger.info("=" * 70)
        logger.info("[ADMINISTRATIVO] ENTRANDO A _run_administrative")
        logger.info(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.info(
            "intent=%s",
            intent,
        )
        logger.info("=" * 70)


        proceso = tracker.get_slot(
            "proceso_activo"
        )
        logger.info(
            "[ADMINISTRATIVO] esperando_tema=%s",
            tracker.get_slot("esperando_tema"),
        )

        logger.info(
            "[ADMINISTRATIVO] tema_actual=%s",
            tracker.get_slot("tema_actual"),
        )

        logger.info(
            "[ADMINISTRATIVO] tema_consulta=%s",
            tracker.get_slot("tema_consulta"),
        )

        # ======================================================
        # PRIMERA CONSULTA ADMINISTRATIVA
        # ======================================================

        if (

            proceso in self.ADMIN_PROCESSES

            and self._is_waiting_for_topic(tracker)

        ):

            nuevo_tema = tracker.latest_message.get(
                "text",
                "",
            ).strip()


            logger.info(
                "[ADMINISTRATIVO] Consulta recibida=%s",
                nuevo_tema,
            )


            eventos = self._build_topic_events_administrative(
                tracker,
                proceso,
            )


            return (

                limpieza

                + eventos

                + self._ejecutar_procesamiento_llm(

                    dispatcher,

                    tracker,

                    self.FLOW_ADMINISTRATIVE,

                    prompt=None,

                    tema_actual=nuevo_tema,

                    tema_consulta=nuevo_tema,

                )

            )


        # ======================================================
        # FLUJO NORMAL ADMINISTRATIVO
        # ======================================================

        return (

            limpieza

            + self._ejecutar_procesamiento_llm(

                dispatcher,

                tracker,

                self.FLOW_ADMINISTRATIVE,

            )

        )


    def _run_academic(
        self,
        dispatcher,
        tracker,
        domain,
        limpieza,
    ) -> List[EventType]:
    
        intent = tracker.get_intent_of_latest_message()
       
        # ======================================================
        # CONTINUAR TEMA (PRIORIDAD)
        # ======================================================


        if intent in (
            "continuar_tema",
            "continuar_tema_si",
        ):

            proceso = tracker.get_slot(
                "proceso_activo"
            )

            if proceso == "faq":

                logger.info(
                    "[FAQ] Continuando pregunta frecuente"
                )

                nuevo_nivel = self._next_explanation_level(
                tracker
                )

                return (

                    limpieza

                    + [

                        SlotSet(
                            "nivel_explicacion",
                            nuevo_nivel,
                        ),

                    ]

                    + self._ejecutar_procesamiento_llm(

                        dispatcher=dispatcher,

                        tracker=tracker,

                        flow=self.FLOW_SUPPORT,

                        prompt=None,

                        nivel_explicacion=nuevo_nivel,

                        tema_actual=tracker.get_slot(
                           "tema_actual"
                        ),

                        tema_consulta=tracker.get_slot(
                            "tema_consulta"
                        ),

                     )

                 )

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
                modo="continuacion",
            )

            logger.info(
                        "[ACADEMICO] Guardando nivel_explicacion=%s",
                        nuevo_nivel,
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
                    
                ]

                + self._ejecutar_procesamiento_llm(

                    dispatcher,
                    tracker,
                    self.FLOW_ACADEMIC,
                    prompt=prompt,
                    nivel_explicacion=nuevo_nivel,
                    tema_actual=tracker.get_slot("tema_actual"),
                    tema_consulta=tracker.get_slot("tema_consulta"),

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

        
        logger.warning(
            "[ENTRY MODO APRENDIZAJE] llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 70)
        logger.error("########## ENTRÉ A MODO APRENDIZAJE ##########")
        logger.warning("proceso_activo=%s", tracker.get_slot("proceso_activo"))
        logger.warning("esperando_tema=%s", tracker.get_slot("esperando_tema"))
        logger.warning("esperando_resolucion=%s", tracker.get_slot("esperando_resolucion"))
        logger.warning("esperando_encuesta_general=%s", tracker.get_slot("esperando_encuesta_general"))
        logger.warning("encuesta_activa=%s", tracker.get_slot("encuesta_activa"))
        logger.warning("intent=%s", intent)
        logger.warning("=" * 70)
        
        logger.error(
            "[ANTES MODO APRENDIZAJE] "
            "esperando_resolucion=%s "
            "encuesta_incompleta=%s "
            "encuesta_activa=%s "
            "intent=%s",
            tracker.get_slot("esperando_resolucion"),
            tracker.get_slot("encuesta_incompleta"),
            tracker.get_slot("encuesta_activa"),
            intent,
        )
        logger.error(
            "[STATE] "
            "esperando_tema=%s "
            "confirmacion_cierre=%s "
            "requested_slot=%s "
            "proceso=%s",
            tracker.get_slot("esperando_tema"),
            tracker.get_slot("confirmacion_cierre"),
            tracker.get_slot("requested_slot"),
            tracker.get_slot("proceso_activo"),
        )

        if (
          
           tracker.get_slot("proceso_activo") == "aprender_tema"

            and not tracker.get_slot("esperando_tema")
            and tracker.latest_message.get("text", "").strip()
            and intent not in (
                "continuar_tema",
                "continuar_tema_si",
                "ir_menu_principal",
                "terminar_conversacion_segura",
                "deny",
                "affirm",
                "respuesta_resuelto_si",
                "respuesta_resuelto_no",
                "respuesta_insatisfecho",
            )
        ):
            logger.error("########## ENTRÉ A MODO APRENDIZAJE ##########")
            texto = tracker.latest_message["text"].strip()

            tema_actual = (
                tracker.get_slot("tema_actual") or ""
            ).strip()


            # --------------------------------------------------
            # Decisión: ¿nuevo tema o continuación?
            # --------------------------------------------------

            logger.warning("=" * 70)
            logger.warning("[DEBUG CAMBIO TEMA]")
            logger.warning("texto=%s", texto)
            logger.warning("tema_actual=%s", tracker.get_slot("tema_actual"))
            logger.warning("proceso_activo=%s", tracker.get_slot("proceso_activo"))
            logger.warning("esperando_tema=%s", tracker.get_slot("esperando_tema"))
            logger.warning("intent=%s", tracker.get_intent_of_latest_message())
            logger.warning("=" * 70)

            es_nuevo = self._is_new_topic(
                tracker,
                texto,
            )

            logger.warning("[DEBUG CAMBIO TEMA] es_nuevo=%s", es_nuevo)

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

                prompt = self._build_continue_prompt(
                    tracker,
                    tema=texto,
                    nivel="basico",
                    modo="tema_nuevo",
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

                        prompt=prompt,
                        
                        nivel_explicacion="basico",

                        tema_actual=texto,
                        
                        tema_consulta=texto,

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
            
            prompt = self._build_continue_prompt(
                tracker,
                tema=tema_actual,
                nivel=tracker.get_slot("nivel_explicacion"),
                modo="subconsulta",
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

                    prompt=prompt,

                    nivel_explicacion=tracker.get_slot(
                        "nivel_explicacion"
                    ),

                    tema_actual=tema_actual,

                    tema_consulta=texto,

                )

            )

        logger.info(
            "[DEBUG] esperando_tema=%s",
            tracker.get_slot("esperando_tema"),
        )

        # ======================================================
        # ESPERANDO QUE EL USUARIO ESCRIBA EL TEMA
        # Primera explicación únicamente para Aprender Tema.
        # ======================================================

        proceso = tracker.get_slot("proceso_activo")

        if proceso == "aprender_tema" and self._is_waiting_for_topic(tracker):

            nuevo_tema = tracker.latest_message.get(
                "text",
                "",
            ).strip()

            logger.info(
                "[TRANSICION] Primera consulta recibida (%s): %s",
                proceso,
                nuevo_tema,
            )

            logger.warning("=" * 80)
            logger.warning("[TRANSICION] ENTRANDO A _build_topic_events")
            logger.warning(
                "proceso=%s",
                proceso,
            )
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

            # --------------------------------------------------
            # Construcción del prompt
            # --------------------------------------------------

            prompt = self._build_continue_prompt(
                tracker,
                tema=nuevo_tema,
                nivel="basico",
                modo="tema_nuevo",
            )

            # --------------------------------------------------
            # Builder por macroflujo
            # --------------------------------------------------

            if proceso == "aprender_tema":

                eventos = self._build_topic_events(
                    tracker,
                    proceso,
                )

            else:

                eventos = []

            # --------------------------------------------------
            # Parámetros específicos por macroflujo
            # --------------------------------------------------

            kwargs = {

                "prompt": prompt,
 
                "tema_actual": nuevo_tema,

                "tema_consulta": nuevo_tema,

            }

            if proceso == "aprender_tema":

                kwargs["nivel_explicacion"] = "basico"

            return (

                limpieza

                + eventos

                + self._ejecutar_procesamiento_llm(

                     dispatcher,

                     tracker,

                     self.FLOW_ACADEMIC,

                     **kwargs,

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

                self.FLOW_ACADEMIC,

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
        dispatcher,
        tracker,
        flow,
        prompt=None,
        nivel_explicacion=None,
        tema_actual=None,
        tema_consulta=None,
    ):
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
        
        logger.warning("=" * 80)
        logger.warning("[DEBUG LLM_REQUEST]")
        logger.warning("llm_request=%s", tracker.get_slot("llm_request"))
        logger.warning("=" * 80)
        
        
        nivel_actual = (
            nivel_explicacion
            if nivel_explicacion is not None
            else tracker.get_slot("nivel_explicacion")
        )

        logger.info(
            "[LLM] nivel_explicacion=%s",
            nivel_actual,
        )
        
        logger.info(
        "[LLM] nivel_explicacion=%s",
        nivel_actual,
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
                       nivel_explicacion=nivel_actual,
                       tema_actual=tema_actual,
                       tema_consulta=tema_consulta,
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
                    nivel_explicacion=nivel_actual,
                    tema_actual=tema_actual,
                    tema_consulta=tema_consulta,
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

            logger.warning("=" * 80)
            logger.warning("[BUILD_PROMPT] CONTEXTO ENVIADO")
            logger.warning("macroflujo=%s", context.get("macroflujo"))
            logger.warning("subflujo=%s", context.get("subflujo"))
            logger.warning("flujo=%s", context.get("flujo"))
            logger.warning("context=%s", context)
            logger.warning("=" * 80)

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

            logger.info("=" * 70)
            logger.info("[LLM] Estado previo a invocar el modelo")
            logger.info("confirmacion_cierre=%s", tracker.get_slot("confirmacion_cierre"))
            logger.info("esperando_resolucion=%s", tracker.get_slot("esperando_resolucion"))
            logger.info("esperando_decision_post_resolucion=%s", tracker.get_slot("esperando_decision_post_resolucion"))
            logger.info("encuesta_activa=%s", tracker.get_slot("encuesta_activa"))
            logger.info("encuesta_incompleta=%s", tracker.get_slot("encuesta_incompleta"))
            logger.info("esperando_encuesta_general=%s", tracker.get_slot("esperando_encuesta_general"))
            logger.info("proceso_activo=%s", tracker.get_slot("proceso_activo"))
            logger.info("flow=%s", flow)
            logger.info("=" * 70)

   
            # =====================================================
            # DETERMINAR EL ESTADO CONVERSACIONAL
            # ANTES DE INVOCAR EL LLM
            # =====================================================

            estado_conversacion = "normal"

            if tracker.get_slot("confirmacion_cierre") == "pendiente":
                estado_conversacion = "confirmacion_cierre"

            elif tracker.get_slot("esperando_resolucion"):
               estado_conversacion = "esperando_resolucion"

            elif tracker.get_slot("esperando_decision_post_resolucion"):
               estado_conversacion = "decision_post_resolucion"

            elif tracker.get_slot("esperando_encuesta_general"):
               estado_conversacion = "encuesta_general"

            elif tracker.get_slot("encuesta_activa"):
               estado_conversacion = "encuesta_activa"

            elif tracker.get_slot("esperando_tema"):
                estado_conversacion = "esperando_tema"

            elif tracker.get_slot("esperando_pregunta_faq"):
                estado_conversacion = "esperando_pregunta_faq"

            elif tracker.get_slot("esperando_pqrsd"):
                estado_conversacion = "esperando_pqrsd"
               
            logger.info(
                "[LLM] Estado conversacional=%s",
                estado_conversacion,
            )
            
            
            # =====================================================
            # Auditoría de coherencia de flujo (NO modifica el flujo)
            # =====================================================

            proceso = tracker.get_slot("proceso_activo")
            macro = context.get("macroflujo")
            sub = context.get("subflujo")

            if proceso:

                esperado = {

                    # ==================================================
                    # Académico
                    # ==================================================

                    "aprender_tema": ("academic", "aprender_tema"),

                    # ==================================================
                    # Soporte
                    # ==================================================

                    "faq": ("support", "faq"),
                    "pqrsd": ("support", "pqrsd"),
                    "crear_caso": ("support", "crear_caso"),
                    "hablar_asesor": ("support", "hablar_asesor"),
                    "contactar_tutor": ("support", "contactar_tutor"),
                    "recuperar_contrasena": ("support", "recuperar_contrasena"),

                   # ==================================================
                   # Administrativo
                   # ==================================================

                   "consultar_estado": ("administrative", "consultar_estado"),
                   "consultar_tutor": ("administrative", "consultar_tutor"),
                   "consultar_horarios": ("administrative", "consultar_horarios"),
                   "consultar_progreso": ("administrative", "consultar_progreso"),
                   "consultar_historial": ("administrative", "consultar_historial"),
                   "consultar_certificados": ("administrative", "consultar_certificados"),
                   "consultar_pagos": ("administrative", "consultar_pagos"),
                   "consultar_notas": ("administrative", "consultar_notas"),
                   "consultar_ficha": ("administrative", "consultar_ficha"),
                   "consultar_inscripciones": ("administrative", "consultar_inscripciones"),

}

                if proceso in esperado:

                    macro_ok, sub_ok = esperado[proceso]

                    if macro != macro_ok or sub != sub_ok:

                        logger.warning(
                            "[FLOW WARNING] proceso_activo=%s recibido=(%s,%s) esperado=(%s,%s)",
                            proceso,
                            macro,
                            sub,
                            macro_ok,
                           sub_ok,
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

                    store_message(
                        text=texto,
                        user_id=tracker.sender_id,
                        session_id=(
                            tracker.get_slot("session_id")
                            or tracker.sender_id
                       ),
                       metadata={
                           "role": "assistant",
                           "flow": flow,
                           "intent_llm": intent_llm,
                       },
                    )

                logger.info(
                    "[LLM] Intent detectado=%s",
                    intent_llm,
                )

            else:

                dispatcher.utter_message(
                    text=respuesta,
                )

                store_message(
                    text=respuesta,
                    user_id=tracker.sender_id,
                    session_id=(
                        tracker.get_slot("session_id")
                        or tracker.sender_id
                    ),
                    metadata={
                        "role": "assistant",
                        "flow": flow,
                    },
                )
                logger.info(
                    "[LLM] Respuesta enviada.",
                )

           
                logger.warning("=" * 80)
                logger.warning("[DEBUG NEXT ACTION]")
                logger.warning("llm_request=%s", llm_request)
                logger.warning("next_action=%s", llm_request.get("next_action") if llm_request else None)
                logger.warning("=" * 80)
                
            # =====================================================
            # Acción posterior definida por llm_request
            # =====================================================
                  
            logger.warning("=" * 80)
            logger.warning("FLOW=%s", flow)
            logger.warning("LLM_REQUEST=%s", llm_request)
            logger.warning("=" * 80)

            # =====================================================
            # Continuación normal del flujo
            # =====================================================

            events = self._build_followup_events(
                flow,
                tracker,
            )


            # =====================================================
            # Postprocesamiento separado por macroflujo
            # =====================================================

            events.extend(

                self._postprocess_flow(

                     flow=flow,

                     tracker=tracker,

                     respuesta=respuesta,

                     llm_request=llm_request,

                )

            )


            # -----------------------------------------------------
            # Mantener proceso_activo SOLO para soporte.
            #
            # No modificarlo porque FAQ y PQRSD dependen
            # de este slot para continuar su flujo.
            # -----------------------------------------------------

            if flow == self.FLOW_SUPPORT:

                proceso = tracker.get_slot(
                    "proceso_activo"
                )

                if proceso:

                    events.insert(

                        0,

                        SlotSet(
                            "proceso_activo",
                            proceso,
                        ),

                    )
            return events

        except Exception:

            logger.exception(
                "[ACTION_HANDLE_WITH_LLM] Error inesperado",
            )

            dispatcher.utter_message(
                text=(
                    "Ocurrió un problema al procesar tu solicitud."
                )
            )

            # =====================================================
            # LIMPIEZA MÍNIMA
            # =====================================================

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

        
        logger.warning("=" * 80)
        logger.warning("[MEMORY_WRAPPER] EJECUTADO")
        logger.warning("intent=%s", tracker.get_intent_of_latest_message())
        logger.warning("sender=%s", tracker.sender_id)
        logger.warning("llm_request=%s", tracker.get_slot("llm_request"))
        logger.warning("proceso_activo=%s", tracker.get_slot("proceso_activo"))
        logger.warning("stack:")
        logger.warning("=" * 80)
        
        try:
            latest = tracker.latest_message or {}

            text = str(
                latest.get("text") or ""
            ).strip()

            if not text:
                return []

            # ==========================================================
            # PROTECCIÓN DE CONTEXTO CONVERSACIONAL
            # ==========================================================

            if tracker.get_slot("confirmacion_cierre") == "pendiente":

                 logger.info(
                     "[MEMORY_WRAPPER] Flujo de confirmación de cierre activo. "
                     "No se procesa memoria adicional."
                 )

                 return []

            elif tracker.get_slot("esperando_resolucion"):

                logger.info(
                    "[MEMORY_WRAPPER] Esperando respuesta de resolución."
                )

                return []

            elif tracker.get_slot("esperando_encuesta_general"):

                logger.info(
                    "[MEMORY_WRAPPER] Esperando inicio de encuesta."
                )

                return []

            elif tracker.get_slot("encuesta_activa"):

                logger.info(
                    "[MEMORY_WRAPPER] Encuesta activa."
                )

                return []

            elif tracker.get_slot("encuesta_incompleta"):

                logger.info(
                    "[MEMORY_WRAPPER] Encuesta incompleta."
                )

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