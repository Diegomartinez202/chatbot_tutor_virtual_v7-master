from __future__ import annotations
import os
import json
import logging
from typing import Text, List, Dict, Any
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import (
    SlotSet,
    ConversationPaused,
    ConversationResumed,
    FollowupAction,
    EventType,
)
from .core.llm_engine import run_llm
from .acciones_encuesta import (
    ActionRegistrarEncuesta,
    obtener_tipo_encuesta,
)
from pymongo import MongoClient
logger = logging.getLogger(__name__)

def get_mongo_collection():
    """Conexión centralizada a MongoDB para limpieza de sesiones."""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "rasa_autosave")
    col_name = os.getenv("MONGO_SECURITY_COLLECTION", "seguridad_autosave")
    
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        return client[db_name][col_name]
    except Exception as e:
        logger.error(f"No se pudo conectar a MongoDB: {e}")
        return None

def limpiar_mongo(tracker: Tracker) -> None:

    coll = get_mongo_collection()

    if coll is None:
        return

    try:
        coll.delete_one({"user_id": tracker.sender_id})
        logger.info("Sesión eliminada de Mongo.")
    except Exception:
        logger.exception("Error limpiando Mongo.")

def limpiar_slots() -> List[EventType]:

    return [

        SlotSet("session_activa", False),

        SlotSet("confirmacion_cierre", None),

        SlotSet("encuesta_activa", False),

        SlotSet("encuesta_incompleta", False),

        SlotSet("esperando_resolucion", False),

        SlotSet("esperando_encuesta_general", False),

        SlotSet("proceso_activo", None),

        SlotSet("esperando_tema", False),

        SlotSet("continuando_tema", False),

        SlotSet("cambio_tema", False),

        SlotSet("tema_actual", None),

        SlotSet("tema_consulta", None),

        SlotSet("tema_anterior", None),

        SlotSet("materia_detectada", None),

        SlotSet("rol_academico", None),

        SlotSet("nivel_explicacion", None),

        SlotSet("ultima_respuesta_llm", None),

        SlotSet("encuesta_tipo", None),

        SlotSet("llm_request", None),

        SlotSet("requested_slot", None),

        SlotSet("autosave_estado", None),

        SlotSet("escalar_humano", False),
    ]

def registrar_encuesta_si_corresponde(tracker: Tracker):

    if not tracker.get_slot("encuesta_activa"):
        return

    try:

        encuesta = {

            "usuario": tracker.sender_id,

            "estado": "pendiente",

            "tipo": tracker.get_slot("encuesta_tipo"),

            "comentario": "Cierre forzado",

        }

        ActionRegistrarEncuesta().registrar_en_base(encuesta)

    except Exception:

        logger.exception("No fue posible registrar encuesta.")

def despedir_usuario(
    dispatcher,
    tracker,
    usar_llm=True,
) -> List[EventType]:

    if not usar_llm:

        dispatcher.utter_message(
            response="utter_despedida"
        )

        return []

    ultimo_intent = (
        tracker.latest_message or {}
    ).get(
        "intent",
        {},
    ).get(
        "name",
        "desconocido",
    )

    safe_slots = {

        k: v

        for k, v in tracker.current_slot_values().items()

        if (
            k not in {

                "user_token",

                "auth_token",

                "password",

                "cedula",

                "email",

                "correo",

                "nombre",

            }

            and v
        )

    }

    return [

        SlotSet(
            "llm_request",
            {
                "instruction": (
                     "Genera únicamente un mensaje de despedida corto (máximo 4 líneas) "
                     "para un estudiante que termina una conversación con el Tutor Virtual del SENA. "
                     "Agradece su visita, deséale éxitos en sus estudios y despídete cordialmente. "
                     "No hagas preguntas. "
                     "No digas que eres una IA. "
                     "No digas que no puedes despedirte. "
                     "No ofrezcas continuar la conversación."
                ),

                "context": {
                    "flujo": "cierre_conversacion",
                    "ultimo_intent": ultimo_intent,
                    "slots": json.dumps(
                        safe_slots
                    )[:500],
                },

                "fallback": (
                    "Gracias por tu tiempo. "
                    "Estaré aquí cuando necesites ayuda."
                ),
                "next_action": (
                    "action_finalizar_cierre"
                ),  
            },
        ),

        FollowupAction(
            "action_handle_with_llm"
        ),

    ]

def ejecutar_cierre_limpio(
    dispatcher,
    tracker,
    finalizar_encuesta=False,
    usar_llm=True,
) -> List[EventType]:

    events: List[EventType] = [

        SlotSet("confirmacion_cierre", None),

        SlotSet("esperando_resolucion", False),

        SlotSet("esperando_decision_post_resolucion", False),

        SlotSet("esperando_encuesta_general", False),

        SlotSet("encuesta_activa", False),

        SlotSet("encuesta_incompleta", False),

        SlotSet("llm_request", None),

    ]

    # --------------------------------------------------------
    # Si el usuario mostró frustración o confusión,
    # ofrecer contacto con un tutor antes del cierre.
    # --------------------------------------------------------
    if tracker.get_slot("emocion_detectada") in {
        "frustrado",
        "confundido",
    }:

        dispatcher.utter_message(
            response="utter_ofrecer_contacto_tutor"
        )

    # --------------------------------------------------------
    # Limpiar información persistida en Mongo.
    # --------------------------------------------------------
    limpiar_mongo(tracker)

    # --------------------------------------------------------
    # Registrar encuesta pendiente si corresponde.
    # --------------------------------------------------------
    if finalizar_encuesta:
        registrar_encuesta_si_corresponde(tracker)


    events.extend(
        despedir_usuario(
            dispatcher,
            tracker,
            usar_llm=usar_llm,
        )
    )
    events.extend(
        limpiar_slots()
    )
    return events

# --- ACCIONES ÚNICAS ---

class ActionConfirmarCierre(Action):

    def name(self) -> Text:
        return "action_confirmar_cierre"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.warning("=" * 80)
        logger.warning("ESTADO DEL TRACKER")
        logger.warning("confirmacion_cierre=%s", tracker.get_slot("confirmacion_cierre"))
        logger.warning("esperando_resolucion=%s", tracker.get_slot("esperando_resolucion"))
        logger.warning("encuesta_activa=%s", tracker.get_slot("encuesta_activa"))
        logger.warning("encuesta_incompleta=%s", tracker.get_slot("encuesta_incompleta"))
        logger.warning("esperando_encuesta_general=%s", tracker.get_slot("esperando_encuesta_general"))
        logger.warning("proceso_activo=%s", tracker.get_slot("proceso_activo"))
        logger.warning("=" * 80)
       
        
        latest = tracker.latest_message or {}

        logger.warning("=" * 70)
        logger.warning("[CIERRE] ActionConfirmarCierre ejecutada")
        logger.warning(
            "texto=%s",
            latest.get("text"),
        )
        logger.warning(
            "intent=%s",
            (latest.get("intent") or {}).get("name"),
        )
        logger.warning("=" * 70)
        
        
        if tracker.get_slot("proceso_activo"):

            dispatcher.utter_message(
                response="utter_confirmar_cierre_con_proceso"
            )

        else:

            dispatcher.utter_message(
                response="utter_confirmar_cierre"
            )
            logger.warning(
                "[ESTADO CIERRE][ActionConfirmarCierre] "
                "confirmacion=%s | "
                "esperando_resolucion=%s | "
                "esperando_decision=%s | "
                "encuesta_activa=%s | "
                "encuesta_incompleta=%s | "
                "esperando_encuesta_general=%s",
                tracker.get_slot("confirmacion_cierre"),
                tracker.get_slot("esperando_resolucion"),
                tracker.get_slot("esperando_decision_post_resolucion"),
                tracker.get_slot("encuesta_activa"),
                tracker.get_slot("encuesta_incompleta"),
                tracker.get_slot("esperando_encuesta_general"),
            )

        return [
            SlotSet("confirmacion_cierre", "pendiente")
        ]

class ActionTerminarConversacionSegura(Action):
    """
    Cierra inmediatamente la conversación cuando el usuario
    decide omitir o rechazar la encuesta de satisfacción.

    No debe utilizarse como flujo normal de finalización,
    ya que éste pasa por ActionDecidirCierre y la encuesta.
    """
    def name(self) -> Text: return "action_terminar_conversacion_segura"
    def run(self, dispatcher, tracker, domain) -> List[EventType]:
        dispatcher.utter_message(response="utter_cierre_confirmado_seguro")
        return ejecutar_cierre_limpio(dispatcher, tracker, finalizar_encuesta=True, usar_llm=False)

class ActionCancelarCierre(Action):

    def name(self) -> Text:
        return "action_cancelar_cierre"

    def run(
        self,
        dispatcher,
        tracker,
        domain,
    ) -> List[EventType]:

        proceso = tracker.get_slot("proceso_activo")

        if proceso == "aprender_tema":

            logger.info(
                "[CIERRE] Reanudando flujo académico."
            )

            dispatcher.utter_message(
                response="utter_ofrecer_continuar"
            )

        else:

            dispatcher.utter_message(
                response="utter_cierre_cancelado"
            )

        eventos = [

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

            ConversationResumed(),

        ]

        return eventos

class ActionDecidirCierre(Action):

    def name(self) -> Text:
        return "action_decidir_cierre"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        
        logger.warning("=" * 80)
        logger.warning("ESTADO DEL TRACKER")
        logger.warning("confirmacion_cierre=%s", tracker.get_slot("confirmacion_cierre"))
        logger.warning("esperando_resolucion=%s", tracker.get_slot("esperando_resolucion"))
        logger.warning("encuesta_activa=%s", tracker.get_slot("encuesta_activa"))
        logger.warning("encuesta_incompleta=%s", tracker.get_slot("encuesta_incompleta"))
        logger.warning("esperando_encuesta_general=%s", tracker.get_slot("esperando_encuesta_general"))
        logger.warning("proceso_activo=%s", tracker.get_slot("proceso_activo"))
        logger.warning("=" * 80)
        
        logger.info(

            "[CIERRE] proceso=%s pending=%s",

            tracker.get_slot("proceso_activo"),

            tracker.get_slot("pending_action"),

        )
        
        logger.info(
            "[CIERRE] encuesta_activa=%s encuesta_incompleta=%s esperando_resolucion=%s proceso=%s",
            tracker.get_slot("encuesta_activa"),
            tracker.get_slot("encuesta_incompleta"),
            tracker.get_slot("esperando_resolucion"),
            tracker.get_slot("proceso_activo"),
        )
        
        # =====================================================
        # Si la encuesta ya estaba iniciada,
        # continuar donde quedó.
        # =====================================================

        if tracker.get_slot("encuesta_activa") or tracker.get_slot("encuesta_incompleta"):

            logger.info(
                "[CIERRE] Reanudando encuesta activa o pendiente."
            )

            return [

                SlotSet(
                    "confirmacion_cierre",
                    None,
                ),

                FollowupAction(
                    "action_guardar_progreso_encuesta"
                )

            ]

        # =====================================================
        # Si existe un proceso activo,
        # lanzar primero la encuesta.
        # =====================================================

        proceso = tracker.get_slot("proceso_activo")

        if proceso:

            logger.info(
                "[CIERRE] Proceso '%s' requiere encuesta.",
                proceso,
            )
            logger.info(
                "[CIERRE] Antes de lanzar encuesta: proceso=%s tema=%s",
                tracker.get_slot("proceso_activo"),
                tracker.get_slot("tema_actual"),
)
            return [

                SlotSet(
                    "confirmacion_cierre",
                    None,
                ),

                SlotSet(
                    "encuesta_activa",
                    True,
                ),

                SlotSet(
                    "encuesta_tipo",
                    obtener_tipo_encuesta(tracker),
                ),

                FollowupAction(
                    "action_preguntar_resolucion",
                ),

            ]

        # =====================================================
        # No había proceso activo.
        # Cierre directo.
        # =====================================================

        logger.info(
            "[CIERRE] No existe proceso activo. Cierre limpio."
        )

        logger.warning(
            "[ESTADO CIERRE][ActionDecidirCierre] "
            "confirmacion=%s | "
            "esperando_resolucion=%s | "
            "esperando_decision=%s | "
            "encuesta_activa=%s | "
            "encuesta_incompleta=%s | "
            "esperando_encuesta_general=%s",
            tracker.get_slot("confirmacion_cierre"),
            tracker.get_slot("esperando_resolucion"),
            tracker.get_slot("esperando_decision_post_resolucion"),
            tracker.get_slot("encuesta_activa"),
            tracker.get_slot("encuesta_incompleta"),
            tracker.get_slot("esperando_encuesta_general"),
         )

        return [

            FollowupAction(
                "action_cierre_limpio"
            ),

        ]
class ActionCierreLimpio(Action):

    def name(self):

        return "action_cierre_limpio"

    def run(self, dispatcher, tracker, domain):

        return ejecutar_cierre_limpio(

            dispatcher,

            tracker,

            finalizar_encuesta=True,

            usar_llm=True,

        )

class ActionFinalizarCierre(Action):
    """
    Ejecuta el cierre definitivo una vez el LLM ya envió
    la despedida al usuario.

    Esta acción limpia el estado conversacional y reinicia
    la conversación para que un nuevo saludo comience desde
    un contexto limpio.
    """

    def name(self) -> Text:
        return "action_finalizar_cierre"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info(
            "[CIERRE] Finalizando conversación."
        )
        logger.warning("=" * 80)
        logger.warning("[FINALIZAR_CIERRE] EJECUTANDO")
        logger.warning("=" * 80)
        events = limpiar_slots()
        logger.error(
            "[RECOVERY] Entrando al cierre definitivo."
        )
        events.append(
            FollowupAction(
                "action_reiniciar_conversacion"
            )
        )

        return events