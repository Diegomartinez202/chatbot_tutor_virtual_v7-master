# ruta: rasa/actions/acciones_seguridad.py
from __future__ import annotations

from typing import Any, Text, Dict, List
import datetime

from pymongo import MongoClient
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType

from .acciones_llm import llm_summarize_with_ollama

# ==========================
# ⚙️ Config Mongo
# ==========================
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "rasa_autosave"
COLLECTION = "seguridad_autosave"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION]


# =====================================================
# 🔌 Notificación de desconexión
# =====================================================
class ActionNotificarDesconexion(Action):
    def name(self) -> Text:
        return "action_notificar_desconexion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        dispatcher.utter_message(response="utter_notificar_desconexion")
        user_id = tracker.sender_id
        estado = {
            "user_id": user_id,
            "timestamp": datetime.datetime.utcnow(),
            "slots": tracker.current_slot_values(),
            "evento": "desconexion",
        }
        collection.update_one({"user_id": user_id}, {"$set": estado}, upsert=True)
        return [SlotSet("evento_seguridad", "desconexion")]


# =====================================================
# ⏱️ Notificación de inactividad
# =====================================================
class ActionNotificarInactividad(Action):
    def name(self) -> Text:
        return "action_notificar_inactividad"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        dispatcher.utter_message(response="utter_notificar_inactividad")
        user_id = tracker.sender_id
        estado = {
            "user_id": user_id,
            "timestamp": datetime.datetime.utcnow(),
            "slots": tracker.current_slot_values(),
            "evento": "inactividad",
        }
        collection.update_one({"user_id": user_id}, {"$set": estado}, upsert=True)
        return [SlotSet("evento_seguridad", "inactividad")]


# =====================================================
# 🔄 Notificación de reconexión (con LLM para explicar)
# =====================================================
class ActionNotificarReconexion(Action):
    def name(self) -> Text:
        return "action_notificar_reconexion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        # Mensaje base que ya tienes
        dispatcher.utter_message(response="utter_notificar_reconexion")

        registro = collection.find_one({"user_id": tracker.sender_id})
        events: List[EventType] = []

        if registro and "slots" in registro:
            # Restaurar slots guardados
            for k, v in registro["slots"].items():
                events.append(SlotSet(k, v))

            # ✨ Mensaje extra con LLM: explicar de forma amable que se restauró la sesión
            try:
                evento_prev = registro.get("evento", "desconocido")
                texto_base = (
                    "El usuario se ha reconectado a la conversación. "
                    f"Había un evento previo registrado: {evento_prev}. "
                    "Genera un mensaje breve, amable y claro para el usuario explicando que "
                    "se restauró su sesión anterior y que puede continuar donde la dejó. "
                    "No menciones detalles específicos de los slots, solo habla en términos generales "
                    "de que se recuperó el progreso guardado."
                )
                contexto_llm = {
                    "flujo": "seguridad_reconexion",
                    "evento_prev": evento_prev,
                    "tiene_sesion_guardada": True,
                }
                mensaje_llm = llm_summarize_with_ollama(texto_base, contexto_llm)
                if mensaje_llm and mensaje_llm.strip():
                    dispatcher.utter_message(text=mensaje_llm.strip())
            except Exception:
                # Si el LLM falla, no rompemos el flujo
                pass

            return events

        # Si no hay registro previo, no hay slots que restaurar
        return events


# =====================================================
# 💾 Guardar estado de seguridad
# =====================================================
class ActionGuardarEstadoSeguridad(Action):
    def name(self) -> Text:
        return "action_guardar_estado_seguridad"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        data = {
            "user_id": tracker.sender_id,
            "slots": tracker.current_slot_values(),
            "timestamp": datetime.datetime.utcnow(),
            "evento": tracker.get_slot("evento_seguridad"),
        }
        collection.update_one({"user_id": tracker.sender_id}, {"$set": data}, upsert=True)
        dispatcher.utter_message(text="💾 Estado de seguridad guardado.")
        return []


# =====================================================
# ♻️ Recuperar estado de seguridad (con LLM suave)
# =====================================================
class ActionRecuperarEstadoSeguridad(Action):
    def name(self) -> Text:
        return "action_recuperar_estado_seguridad"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        registro = collection.find_one({"user_id": tracker.sender_id})
        if registro and "slots" in registro:
            dispatcher.utter_message(text="🔄 Restaurando sesión guardada...")

            events: List[EventType] = [
                SlotSet(k, v) for k, v in registro["slots"].items()
            ]

            # ✨ Mensaje adicional amigable con LLM
            try:
                evento_prev = registro.get("evento", "desconocido")
                texto_base = (
                    "Se ha recuperado un estado de seguridad previo para el usuario. "
                    f"El último evento registrado fue: {evento_prev}. "
                    "Genera un mensaje corto y claro para el usuario explicando que se cargó su sesión guardada, "
                    "que su progreso se ha restaurado y que puede continuar con su consulta o proceso. "
                    "No menciones datos sensibles ni detalles específicos de los slots."
                )
                contexto_llm = {
                    "flujo": "seguridad_recuperar_estado",
                    "evento_prev": evento_prev,
                    "tiene_sesion_guardada": True,
                }
                mensaje_llm = llm_summarize_with_ollama(texto_base, contexto_llm)
                if mensaje_llm and mensaje_llm.strip():
                    dispatcher.utter_message(text=mensaje_llm.strip())
            except Exception:
                pass

            return events

        dispatcher.utter_message(text="No se encontró sesión guardada previa.")
        return []
