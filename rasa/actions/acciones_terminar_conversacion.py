from __future__ import annotations
import os
import json
import logging
from typing import Text, List, Dict, Any
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, ConversationPaused, ConversationResumed, EventType
from .core.llm_engine import run_llm
from .acciones_encuesta import ActionRegistrarEncuesta
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

def ejecutar_cierre_limpio(dispatcher, tracker, finalizar_encuesta=False, usar_llm=True):
    
    slot_emocion = tracker.get_slot("emocion_detectada")
    if slot_emocion and str(slot_emocion).strip().lower() in ("frustrado", "confundido"):
        dispatcher.utter_message(response="utter_ofrecer_contacto_tutor")

    coll = get_mongo_collection() 

    if coll is not None and tracker.sender_id:
        try:
            coll.delete_one({"user_id": tracker.sender_id})
        except Exception:
           
           logger.error("Error limpiando sesión en Mongo durante el cierre")
    events = [
        SlotSet("session_activa", False), SlotSet("confirmacion_cierre", None),
        SlotSet("encuesta_activa", False), SlotSet("encuesta_incompleta", False),
        SlotSet("proceso_activo", None), SlotSet("escalar_humano", False),
        SlotSet("autosave_estado", None), SlotSet("encuesta_tipo", None)
    ]

    if finalizar_encuesta and tracker.get_slot("encuesta_activa"):
        try:
            encuesta_data = {"usuario": tracker.sender_id, "estado": "pendiente", 
                             "tipo": tracker.get_slot("encuesta_tipo"), "comentario": "Cierre forzado"}
            ActionRegistrarEncuesta().registrar_en_base(encuesta_data)
        except Exception:
            logger.exception("Error guardando encuesta en cierre")

    if usar_llm:
        ultimo_intent = (tracker.latest_message or {}).get("intent", {}).get("name", "desconocido")
        safe_slots = {k: v for k, v in tracker.current_slot_values().items() 
                      if k not in {"user_token", "auth_token", "password", "cedula", "email", "correo", "nombre"} and v}
        
        try:
            mensaje = run_llm(prompt="Despide al estudiante de forma profesional.", tracker=tracker,
                              context={"ultimo_intent": ultimo_intent, "slots": json.dumps(safe_slots)[:500]},
                              fallback="Gracias por tu tiempo. Estaré aquí cuando necesites ayuda.")
            dispatcher.utter_message(text=mensaje if isinstance(mensaje, str) else "¡Hasta pronto!")
        except Exception:
            dispatcher.utter_message(response="utter_despedida")

    events.append(ConversationPaused())
    return events

# --- ACCIONES ÚNICAS ---

class ActionConfirmarCierre(Action):
    def name(self) -> Text: return "action_confirmar_cierre"
    def run(self, dispatcher, tracker, domain) -> List[EventType]:
        dispatcher.utter_message(response="utter_confirmar_cierre")
        return [SlotSet("confirmacion_cierre", "pendiente")]

class ActionFinalizarConversacion(Action):
    def name(self) -> Text: return "action_finalizar_conversacion"
    def run(self, dispatcher, tracker, domain) -> List[EventType]:
        return ejecutar_cierre_limpio(dispatcher, tracker, finalizar_encuesta=True)

class ActionTerminarConversacionSegura(Action):
    def name(self) -> Text: return "action_terminar_conversacion_segura"
    def run(self, dispatcher, tracker, domain) -> List[EventType]:
        dispatcher.utter_message(response="utter_cierre_confirmado_seguro")
        return ejecutar_cierre_limpio(dispatcher, tracker, finalizar_encuesta=True, usar_llm=False)

class ActionCancelarCierre(Action):
    def name(self) -> Text: return "action_cancelar_cierre"
    def run(self, dispatcher, tracker, domain) -> List[EventType]:
        dispatcher.utter_message(response="utter_cierre_cancelado")
        return [SlotSet("confirmacion_cierre", None), ConversationResumed()]