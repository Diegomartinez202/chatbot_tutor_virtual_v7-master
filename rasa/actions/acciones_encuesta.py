# ruta: rasa/actions/acciones_encuesta.py
from __future__ import annotations

from typing import Dict, List, Any, Text
import os
import json
import datetime
import logging

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import SlotSet, FollowupAction

from .core.llm_engine import run_llm
import hashlib
import threading

logger = logging.getLogger(__name__)

_DATA_DIR = "data"
_ENC_FILE = os.path.join(_DATA_DIR, "encuestas.jsonl")

_FILE_LOCK = threading.Lock()

MAX_COMMENT_LENGTH = 1000
MAX_STORAGE_COMMENT_LENGTH = 2000

# ==========================================================
# CATÁLOGO CENTRAL DE ENCUESTAS POR MÓDULO
# ==========================================================

ENCUESTAS_POR_MODULO = {

    # -------------------------
    # Académico
    # -------------------------
    "aprender_tema": "satisfaccion",

    "consultar_horarios": "satisfaccion",

    "consultar_progreso": "satisfaccion",

    "historial_academico": "satisfaccion",

    "estado_estudiante": "satisfaccion",

    # -------------------------
    # Soporte
    # -------------------------

    "soporte_tecnico": "satisfaccion",

    "pqrs": "satisfaccion",

    "correo": "satisfaccion",

    "tutor": "satisfaccion",

    "humano": "satisfaccion",

    # -------------------------
    # Consulta general
    # -------------------------

    None: "general",

    "general": "general",
}

def obtener_tipo_encuesta(tracker: Tracker) -> str:
    """
    Determina qué encuesta corresponde según el módulo activo.

    Retorna:
        satisfaccion
        general
    """

    proceso = tracker.get_slot("proceso_activo")

    return ENCUESTAS_POR_MODULO.get(
        proceso,
        "general",
    )

def _ensure_store() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.exists(_ENC_FILE):
        with open(_ENC_FILE, "w", encoding="utf-8") as f:
            f.write("")

def _append_jsonl(record: Dict[str, Any]) -> None:
    _ensure_store()

    with _FILE_LOCK:
        with open(
            _ENC_FILE,
            "a",
            encoding="utf-8",
        ) as f:
            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )


def _safe_user_id(tracker: Tracker) -> str:
    sender_id = str(tracker.sender_id or "")

    if not sender_id:
        return "anonimo"

    return hashlib.sha256(
        sender_id.encode("utf-8")
    ).hexdigest()[:16]

class ActionRegistrarEncuesta(Action):

    def name(self) -> str:
        return "action_registrar_encuesta"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[str, Any],
    ) -> List[EventType]:

        # ==========================================================
        # 1. RECUPERAR RESPUESTAS DE LA ENCUESTA
        # ==========================================================

        satisfaccion = (
            tracker.get_slot("nivel_satisfaccion")
            or tracker.get_slot("satisfaccion")
            or "no_especificado"
        )

        comentario = (
            tracker.get_slot("comentario")
            or tracker.latest_message.get("text", "sin comentario")
        )

        comentario = comentario[:MAX_STORAGE_COMMENT_LENGTH]

        usuario = _safe_user_id(tracker)

        fecha = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()

        registro = {
            "usuario": usuario,
            "satisfaccion": satisfaccion,
            "comentario": comentario,
            "fecha": fecha,
        }

        # ==========================================================
        # 2. GUARDAR ENCUESTA
        # ==========================================================

        try:

            _append_jsonl(registro)

            logger.info(
                "[ENCUESTA] Encuesta registrada correctamente."
            )

        except Exception:

            logger.exception(
                "[ENCUESTA] error guardando encuesta"
            )

        # ==========================================================
        # 3. LIMPIEZA DE SLOTS
        # ==========================================================

        events: List[EventType] = [

            SlotSet(
               
               "encuesta_incompleta",
                False,
            ),

            SlotSet(
               "encuesta_activa",
               False,
            ),
            SlotSet(
                "nivel_satisfaccion",
                None,
            ),

            SlotSet(
                "comentario",
                None,
            ),

            SlotSet(
                "encuesta_tipo",
                None,
            ),

            SlotSet(
                "calificacion_numerica",
                None,
            ),

            SlotSet(
                "problema_resuelto",
                None,
            ),

            # ======================================================
            # Solicitud para ActionHandleWithLLM
            # ======================================================

            SlotSet(
                "llm_request",
                {
                    "instruction": (
                        f"Se registró una encuesta de satisfacción "
                        f"con nivel '{satisfaccion}'. "
                        f"Comentario del usuario: \"{comentario}\". "
                        "Agradece de forma amable el tiempo del usuario "
                        "y recuérdale que su opinión ayuda a mejorar."
                    ),

                    "context": {
                        "flujo": "guardian_encuesta",
                        "nivel_satisfaccion": satisfaccion,
                        "tiene_comentario": bool(
                            comentario and comentario.strip()
                        ),
                    },

                    "fallback": (
                        "✅ Gracias por responder la encuesta. "
                        "Tu opinión nos ayuda a mejorar continuamente."
                    ),

                    "next_action": "action_preguntar_encuesta_general",
              
                },
            ),

           
            FollowupAction(
                "action_handle_with_llm"
            ),
        ]

        return events


class ActionGuardarFeedback(Action):

    def name(self) -> str:
        return "action_guardar_feedback"

    def run(
        self,
        dispatcher,
        tracker,
        domain,
    ):

        feedback_tipo = tracker.get_slot(
            "feedback_tipo"
        )

        feedback_texto = tracker.get_slot(
            "feedback_texto"
        )

        usuario = _safe_user_id(tracker)

        fecha = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()

        try:

            _append_jsonl(
                {
                    "usuario": usuario,
                    "tipo": feedback_tipo,
                    "feedback": feedback_texto,
                    "fecha": fecha,
                }
            )

        except Exception:
            logger.exception(
                "[FEEDBACK] error guardando feedback"
            )
            logger.warning("=" * 80)
            logger.warning("ACTION_GUARDAR_FEEDBACK EJECUTADA")
            logger.warning("=" * 80)
        dispatcher.utter_message(
            response="utter_gracias_retroalimentacion"
        )

        return [
            SlotSet("feedback_tipo", None),
            SlotSet("feedback_texto", None),
            SlotSet("proceso_activo", None),

            SlotSet("tema_actual", None),

            SlotSet("tema_consulta", None),

            SlotSet("materia_detectada", None),

            SlotSet("rol_academico", None),

            SlotSet("esperando_tema", False),

            SlotSet("llm_request", None),

            SlotSet("ultima_respuesta_llm", None),
        ]

class ActionPreguntarResolucion(Action):

    def name(self) -> str:
        return "action_preguntar_resolucion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[str, Any],
    ) -> List[EventType]:

        logger.info(
            "[ENCUESTA] Preguntando si el problema fue resuelto."
        )

        dispatcher.utter_message(
            response="utter_esta_resuelto"
        )

        return [

            SlotSet(
                "encuesta_incompleta",
                True,
            ),

            SlotSet(
                "esperando_resolucion",
                True,
            ),

            SlotSet(
                "encuesta_tipo",
                obtener_tipo_encuesta(tracker),
            ),

            FollowupAction(
                "action_listen",
            ),

        ]

class ActionSetEncuestaTipo(Action):
    def name(self) -> Text:
        return "action_set_encuesta_tipo"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        """
        Marca el tipo de encuesta según el intent detectado.

        Valores válidos (alineados con domain.yml):
        - "positiva"
        - "negativa"
        - "neutra"
        """

        intent = (tracker.latest_message.get("intent") or {}).get("name", "")

        if intent == "respuesta_satisfecho":
            tipo = "positiva"
        elif intent == "respuesta_insatisfecho":
            tipo = "negativa"
        else:
            tipo = "neutra"

        logger.info(
    "[ActionSetEncuestaTipo] intent=%s -> encuesta_tipo=%s",
    intent,
    tipo,
)
        return [SlotSet("encuesta_tipo", tipo)]

class ValidateEncuestaSatisfaccionForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_encuesta_satisfaccion_form"


    def validate_nivel_satisfaccion(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[str, Any],
    ) -> Dict[Text, Any]:
        v = (value or "").strip().lower()

        validos = {
            "excelente",
            "buena",
            "regular",
            "mala",
            "satisfecho",
            "neutral",
            "insatisfecho",
        }

        if v in validos:
            return {"nivel_satisfaccion": v}

        dispatcher.utter_message(
            text=(
                "💡 Usa una opción válida para la atención recibida: "
                "satisfecho, neutral o insatisfecho. "
                "Si quieres, también puedes responder excelente, buena, regular o mala."
            )
        )
        return {"nivel_satisfaccion": None}

    def validate_problema_resuelto(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[str, Any],
    ) -> Dict[Text, Any]:
        v = (value or "").strip().lower()

        if v in {"si", "sí", "claro", "correcto"}:
            return {"problema_resuelto": "si"}
        if v in {"no", "no del todo", "todavia no", "todavía no"}:
            return {"problema_resuelto": "no"}

        dispatcher.utter_message(
            text="💡 Respóndeme con 'sí' o 'no', para saber si pudimos resolver tu problema."
        )
        return {"problema_resuelto": None}

    def validate_calificacion_numerica(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[str, Any],
    ) -> Dict[Text, Any]:
        raw = str(value or "").strip().lower()

        palabras_a_numero = {
            "uno": "1",
            "dos": "2",
            "tres": "3",
            "cuatro": "4",
            "cinco": "5",
        }

        if raw in palabras_a_numero:
            raw = palabras_a_numero[raw]

        if raw in {"1", "2", "3", "4", "5"}:
 
            return {"calificacion_numerica": raw}

        dispatcher.utter_message(
            text=(
                "💡 Por favor responde con un número del 1 al 5, donde:\n"
                "1 = muy poco satisfecho\n"
                "5 = muy satisfecho"
            )
        )
        return {"calificacion_numerica": None}

    def validate_comentario(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[str, Any],
    ) -> Dict[Text, Any]:
        v = (value or "").strip()
        if not v:
            dispatcher.utter_message(
                text="📝 Déjanos un breve comentario (puede ser una frase corta)."
            )
            return {"comentario": None}
        if len(v) > MAX_COMMENT_LENGTH:
            dispatcher.utter_message(
                text="✂️ El comentario es muy largo. Resume en menos de 1000 caracteres."
            )
            return {"comentario": None}
        return {"comentario": v}

# =====================================================================
# 3. ACCIÓN: PROCESAR RESPUESTA A "¿QUEDÓ RESUELTO?"
# =====================================================================

class ActionProcesarRespuestaResolucion(Action):

    def name(self) -> Text:
        return "action_procesar_respuesta_resolucion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        latest = tracker.latest_message or {}

        ultimo_intent = (
            latest.get("intent", {}) or {}
        ).get("name", "")

        logger.info(
            "[ActionProcesarRespuestaResolucion] intent=%s",
            ultimo_intent,
        )

        # ==========================================================
        # El usuario indicó que NO quedó resuelto
        # ==========================================================

        if ultimo_intent in [
            "respuesta_resuelto_no",
            "respuesta_insatisfecho",  
            "deny",                    
        ]: 
            botones = [

                {
                    "title": "📚 Seguir con el tema",
                    "payload": "/continuar_tema",
                },

                {
                    "title": "🏠 Menú Principal",
                    "payload": "/menu_principal",
                },

                {
                    "title": "🚪 Salir y Calificar Bot",
                    "payload": "/forzar_salida",
                },

            ]

            dispatcher.utter_message(
                text=(
                    "Lamento que no hayamos resuelto tu inquietud por completo. "
                    "¿Qué te gustaría hacer ahora?"
                ),
                buttons=botones,
            )

            return [

                SlotSet(
                    "esperando_resolucion",
                    False,
                ),
                
                SlotSet(
                    "encuesta_incompleta",
                    True,
                ),

            ]

        # ==========================================================
        # Usuario indica que SÍ quedó resuelto
        # ==========================================================

        elif ultimo_intent in [
            "respuesta_resuelto_si",
            "affirm",      
        ]:

            logger.info(
                "[ENCUESTA] Iniciando encuesta de satisfacción."
            )

            return [

                SlotSet(
                    "esperando_resolucion",
                    False,
                ),
                
                SlotSet(
                    "encuesta_activa",
                    True,
                ),

                FollowupAction(
                    "encuesta_satisfaccion_form",
                ),

            ]

        # ==========================================================
        # Intent inesperado
        # ==========================================================

        logger.warning(
            "[ENCUESTA] Intent inesperado: %s",
            ultimo_intent,
        )

        return []


# =====================================================================
# PREGUNTAR SI EL USUARIO DESEA EVALUAR EL CHATBOT
# =====================================================================

class ActionPreguntarEncuestaGeneral(Action):

    def name(self) -> Text:
        return "action_preguntar_encuesta_general"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        # ==========================================================
        # Determinar desde qué módulo viene el usuario
        # ==========================================================

        proceso = tracker.get_slot("proceso_activo")
        tipo_encuesta = tracker.get_slot("encuesta_tipo")

        # ==========================================================
        # Personalizar el mensaje
        # ==========================================================

        if proceso == "aprender_tema":

            mensaje = (
                "😊 Muchas gracias por responder la encuesta de satisfacción académica.\n\n"
                "¿Nos ayudarías con una breve evaluación del Bot Tutor Virtual?\n\n"
                "Tu opinión nos ayuda a seguir mejorando la experiencia de aprendizaje para todos los estudiantes."
            )

        elif proceso in [
            "soporte_tecnico",
            "pqrs",
            "correo",
            "humano",
        ]:

            mensaje = (
                "😊 Gracias por responder la encuesta del servicio de soporte.\n\n"
                "¿Te gustaría dedicar unos segundos para evaluar tu experiencia general con el Bot Tutor Virtual?"
            )

        else:

            mensaje = (
                "😊 Gracias por responder la encuesta.\n\n"
                "¿Podrías dedicar unos segundos para evaluar el Bot Tutor Virtual?\n\n"
                "Tu opinión nos ayuda a seguir mejorando nuestros servicios."
            )

        # ==========================================================
        # Botones
        # ==========================================================

        botones = [

            {
                "title": "✅ Sí",
                "payload": "/affirm",
            },

            {
                "title": "❌ No, gracias",
                "payload": "/deny",
            },

        ]

        dispatcher.utter_message(
            text=mensaje,
            buttons=botones,
        )

        return [

            SlotSet(
                "esperando_encuesta_general",
                True,
            ),

            SlotSet("confirmacion_cierre", None),

            FollowupAction("action_listen"),
        ]


# =====================================================================
# 4. NUEVA ACCIÓN: LANZAR EVALUACIÓN DE USABILIDAD GENERAL DEL BOT
# =====================================================================
class ActionLanzarEncuestaGeneral(Action):
    def name(self) -> Text:
        return "action_lanzar_encuesta_general"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        logger.warning("=" * 80)
        logger.warning("[ENCUESTA GENERAL] EJECUTANDO ACTION")
        logger.warning("=" * 80)
        """
        Lanza los componentes interactivos finales para evaluar el rendimiento global del sistema.
        """
        botones_calificacion = [
            {"title": "⭐ 1", "payload": "/calificar_bot{\"nota\": \"1\"}"},
            {"title": "⭐⭐ 2", "payload": "/calificar_bot{\"nota\": \"2\"}"},
            {"title": "⭐⭐⭐ 3", "payload": "/calificar_bot{\"nota\": \"3\"}"},
            {"title": "⭐⭐⭐⭐ 4", "payload": "/calificar_bot{\"nota\": \"4\"}"},
            {"title": "⭐⭐⭐⭐⭐ 5", "payload": "/calificar_bot{\"nota\": \"5\"}"}
        ]
        
        dispatcher.utter_message(
            text=(
                "⭐ Para finalizar, ¿cómo calificarías tu experiencia general "
                "utilizando el Bot Tutor Virtual SENA?"
            ),
            buttons=botones_calificacion,
        )

        return [

            SlotSet(
                "esperando_encuesta_general",
                True,
            ),
            SlotSet(
                "confirmacion_cierre",
                None,
            ),

            SlotSet("proceso_activo", None),

            FollowupAction("action_listen"),

        ]

class ActionGuardarCalificacionGeneral(Action):

    def name(self):
        return "action_guardar_calificacion_general"

    def run(self, dispatcher, tracker, domain):

        nota = next(

            (
                e.get("value")
                for e in tracker.latest_message.get("entities", [])
                if e.get("entity") == "nota"
            ),

            tracker.get_slot("nota"),
        )

        logger.info(
            "[ENCUESTA GENERAL] Calificación=%s",
            nota,
        )

        registro = {
            "usuario": _safe_user_id(tracker),
            "tipo": "evaluacion_general",
            "calificacion": nota,
            "fecha": datetime.datetime.now(
                datetime.timezone.utc
            ).isoformat(),
        }

        try:
            _append_jsonl(registro)

        except Exception:
            logger.exception(
                "[ENCUESTA GENERAL]"
            )
        dispatcher.utter_message(
            text="⭐ ¡Gracias por calificar el sistema! Tu opinión nos ayuda a seguir mejorando."
        )
        return [

            SlotSet("nota", None),

            SlotSet("proceso_activo", None),

            SlotSet("tema_actual", None),

            SlotSet("tema_consulta", None),

            SlotSet("materia_detectada", None),

            SlotSet("ultima_respuesta_llm", None),

            SlotSet("nivel_explicacion", None),

            SlotSet("esperando_encuesta_general", False),

            SlotSet("llm_request", None),

            FollowupAction("action_cierre_limpio"),

        ]
