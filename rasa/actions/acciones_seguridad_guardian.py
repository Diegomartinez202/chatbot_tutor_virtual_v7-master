# rasa/actions/acciones_seguridad_guardian.py
from __future__ import annotations
import os, datetime
from typing import Any, Dict, List, Text
from pymongo import MongoClient
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, ConversationPaused, ConversationResumed, EventType
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from utils.mongo_autosave import guardar_autosave, log_event  # ← tus utilidades

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB", "chatbot_tutor_virtual")
AUTOSAVE_COLLECTION = os.getenv("MONGO_AUTOSAVE_COLLECTION", "autosaves")

_client = MongoClient(MONGO_URI)
_db     = _client[MONGO_DB]
_autos  = _db[AUTOSAVE_COLLECTION]

def _log(usuario: str, evento: str, estado: str, detalle: Dict[str, Any] | None = None):
    log_event(usuario, evento, estado, detalle)

class ActionGuardianGuardarProgreso(Action):
    def name(self) -> Text: return "action_guardian_guardar_progreso"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        dispatcher.utter_message(response="utter_guardando_progreso")
        usuario = tracker.sender_id
        payload = {"user_id": usuario, "slots": tracker.current_slot_values(), "estado": "guardado",
                   "updated_at": datetime.datetime.utcnow()}
        _autos.update_one({"user_id": usuario}, {"$set": payload}, upsert=True)
        _log(usuario, "guardian_guardar_progreso", "ok", {"slots": len(payload["slots"] or {})})
        dispatcher.utter_message(text="✅ Progreso guardado correctamente.")
        return [SlotSet("encuesta_activa", True)]

class ActionGuardianCargarProgreso(Action):
    def name(self) -> Text: return "action_guardian_cargar_progreso"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        usuario = tracker.sender_id
        doc = _autos.find_one({"user_id": usuario})
        if doc and "slots" in doc:
            _log(usuario, "guardian_cargar_progreso", "ok", {"existe": True})
            dispatcher.utter_message(text="🔄 Cargando tu progreso guardado…")
            return [SlotSet(k, v) for k, v in (doc["slots"] or {}).items()]
        _log(usuario, "guardian_cargar_progreso", "ok", {"existe": False})
        dispatcher.utter_message(text="No se encontró información previa.")
        return []

class ActionGuardianPausar(Action):
    def name(self) -> Text: return "action_guardian_pausar"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        usuario = tracker.sender_id
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(response="utter_confirmar_cierre")
            _log(usuario, "guardian_pausar_requiere_confirmacion", "ok")
            return []
        dispatcher.utter_message(response="utter_cierre_confirmado")
        _log(usuario, "guardian_pausar", "ok")
        return [ConversationPaused()]

class ActionGuardianReanudar(Action):
    def name(self) -> Text: return "action_guardian_reanudar"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        usuario = tracker.sender_id
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(text="🔁 Retomamos donde quedaste.")
            _log(usuario, "guardian_reanudar", "ok", {"encuesta_activa": True})
            return [ConversationResumed()]
        dispatcher.utter_message(text="No había nada pendiente, puedes continuar.")
        _log(usuario, "guardian_reanudar", "ok", {"encuesta_activa": False})
        return []

class ActionGuardianReset(Action):
    def name(self) -> Text: return "action_guardian_reset"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        usuario = tracker.sender_id
        _autos.delete_one({"user_id": usuario})
        _log(usuario, "guardian_reset", "ok")
        dispatcher.utter_message(text="🧹 Datos temporales eliminados.")
        return [SlotSet("encuesta_activa", False), SlotSet("autosave_estado", None)]

class ActionRegistrarEncuesta(Action):
    def name(self) -> str: return "action_registrar_encuesta"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        data = {
            "usuario": tracker.sender_id,
            "ultimo_intent": tracker.latest_message.get("intent", {}).get("name"),
            "texto": tracker.latest_message.get("text"),
            "slots": tracker.current_slot_values(),
        }
        guardar_autosave(tracker.sender_id, data)
        dispatcher.utter_message(text="✅ Registro de satisfacción guardado y autosave completado.")
        _log(tracker.sender_id, "registrar_encuesta", "ok", {"intent": data["ultimo_intent"]})
        return []

class ActionGuardarAutosave(Action):
    def name(self) -> Text:
        return "action_guardar_autosave"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        client = GuardianClient(
            base_url="http://autosave-guardian:8080",
            username="admin",
            password="admin123",
        )

        # Datos mínimos a guardar
        payload = {
            "latest_intent": tracker.latest_message.get("intent", {}).get("name"),
            "latest_text": tracker.latest_message.get("text"),
            "slots": tracker.current_slot_values(),
        }

        ok = client.autosave_create(tracker.sender_id, payload)
        if ok:
            dispatcher.utter_message(text="Autosave guardado ✅")
        else:
            dispatcher.utter_message(text="No se pudo guardar el autosave ❌ (no bloqueante)")
        return []