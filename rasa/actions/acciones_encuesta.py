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

from .core.llm_engine import run_llm
import hashlib
import threading

logger = logging.getLogger(__name__)

_DATA_DIR = "data"
_ENC_FILE = os.path.join(_DATA_DIR, "encuestas.jsonl")

_FILE_LOCK = threading.Lock()

MAX_COMMENT_LENGTH = 1000
MAX_STORAGE_COMMENT_LENGTH = 2000

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

        try:
            _append_jsonl(registro)
        except Exception:
            logger.exception(
                "[ENCUESTA] error guardando encuesta"
            )

        texto_base = (
            f"Se registró una encuesta de satisfacción con nivel '{satisfaccion}'. "
            f"Comentario del usuario: \"{comentario}\". "
            "Agradece de forma amable el tiempo del usuario y recuérdale que su opinión ayuda a mejorar."
        )

        contexto_llm = {
            "flujo": "encuesta_satisfaccion",
            "nivel_satisfaccion": satisfaccion,
            "tiene_comentario": bool(
                comentario and comentario.strip()
            ),
        }

        mensaje_final = run_llm(
        prompt=texto_base,
        tracker=tracker,
        context=contexto_llm,
        fallback=texto_base,
        )

        dispatcher.utter_message(text=mensaje_final)

        return [
            SlotSet("encuesta_incompleta", False),
            SlotSet("encuesta_activa", False),
            SlotSet("proceso_activo", None),
            FollowupAction("action_lanzar_encuesta_general")
        ]


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

        dispatcher.utter_message(
            response="utter_gracias_retroalimentacion"
        )

        return [
            SlotSet("feedback_tipo", None),
            SlotSet("feedback_texto", None),
        ]

class ActionPreguntarResolucion(Action):
    def name(self) -> str:
        return "action_preguntar_resolucion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        dispatcher.utter_message(response="utter_esta_resuelto")
        return [
            SlotSet("encuesta_incompleta", True),
            SlotSet("proceso_activo", "encuesta_satisfaccion"),
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
# 3. NUEVA ACCIÓN: MITIGACIÓN Y CONTROL EN CASO DE RESPUESTA 'NO'
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
        """
        Intercepta el intent del usuario. Si persiste la duda, frena la salida
        y despliega las opciones de redirección del flujo académico.
        """
        ultimo_intent = tracker.latest_message.get("intent", {}).get("name", "")
        
        logger.info("[ActionProcesarRespuestaResolucion] El usuario respondió con intent=%s", ultimo_intent)

        if ultimo_intent in ["respuesta_insatisfecho", "negar"]:
            botones = [
                {"title": "📚 Seguir con el tema", "payload": "/continuar_tema"},
                {"title": "🏠 Menú Principal", "payload": "/menu_principal"},
                {"title": "🚪 Salir y Calificar Bot", "payload": "/forzar_salida"}
            ]
            dispatcher.utter_message(
                text="Lamento que no hayamos resuelto tu inquietud por completo. ¿Qué te gustaría hacer ahora?",
                buttons=botones
            )
            return [SlotSet("encuesta_incompleta", True)]
        
        else:
            # Si el usuario responde afirmativamente, se procesa la encuesta de satisfacción corta
            return [FollowupAction("encuesta_satisfaccion_form")]


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
            text="Por último, ayúdanos calificando tu experiencia general usando el Sistema Bot Tutor Virtual SENA:",
            buttons=botones_calificacion
        )
        return []


class ActionVerificarEstadoEncuesta(Action):
    def name(self) -> Text:
        return "action_verificar_estado_encuesta"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        """Verifica si hay una encuesta activa o pendiente y actualiza el slot `encuesta_activa`."""

        encuesta_activa_slot = tracker.get_slot("encuesta_activa")
        encuesta_incompleta = tracker.get_slot("encuesta_incompleta")
        autosave_estado = tracker.get_slot("autosave_estado")

        nivel_satisfaccion = tracker.get_slot("nivel_satisfaccion")
        encuesta_tipo = tracker.get_slot("encuesta_tipo")
        comentario = tracker.get_slot("comentario")

        autosave_tiene_encuesta = False
        if isinstance(autosave_estado, str) and autosave_estado.strip():
            autosave_tiene_encuesta = "encuesta" in autosave_estado.lower()

        encuesta_slots = [nivel_satisfaccion, encuesta_tipo, comentario]
        algun_dato_encuesta = any(
            s is not None and str(s).strip() != "" for s in encuesta_slots
        )
        encuesta_completa = all(
            s is not None and str(s).strip() != "" for s in encuesta_slots
        )
        encuesta_pendiente = algun_dato_encuesta and not encuesta_completa

        hay_encuesta_activa = (
            bool(encuesta_activa_slot)
            or bool(encuesta_incompleta)
            or autosave_tiene_encuesta
            or encuesta_pendiente
        )

        logger.info(
            "[action_verificar_estado_encuesta] encuesta_activa_slot=%r, "
            "encuesta_incompleta=%r, autosave_estado_present=%r, "
            "autosave_tiene_encuesta=%r, algun_dato_encuesta=%r, "
            "encuesta_completa=%r, encuesta_pendiente=%r -> hay_encuesta_activa=%r",
            encuesta_activa_slot,
            encuesta_incompleta,
            bool(autosave_estado),
            autosave_tiene_encuesta,
            algun_dato_encuesta,
            encuesta_completa,
            encuesta_pendiente,
            hay_encuesta_activa,
        )
        proceso_actual = tracker.get_slot("proceso_activo")
        if proceso_actual in ["aprender_tema", "preguntas_frecuentes"]:
            dispatcher.utter_message(text="Veo que tienes una encuesta o proceso pendiente. Podemos retomarlo antes de cerrar.")
            eventos: List[EventType] = [SlotSet("encuesta_activa", True), FollowupAction("action_preguntar_resolucion")]
            return eventos


        if hay_encuesta_activa:
            dispatcher.utter_message(
                text=(
                    "Veo que tienes una encuesta o proceso pendiente. "
                    "Podemos retomarlo antes de cerrar."
                )
            )
        else:
            dispatcher.utter_message(
                text="No tienes encuestas activas. Podemos cerrar la conversación de forma segura."
            )

        eventos: List[EventType] = [SlotSet("encuesta_activa", hay_encuesta_activa)]

        eventos.append(SlotSet("encuesta_incompleta", encuesta_pendiente))

        return eventos
