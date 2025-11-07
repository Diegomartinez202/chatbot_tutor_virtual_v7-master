from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ConversationPaused, ConversationResumed
from datetime import datetime
from .acciones_encuesta import ActionRegistrarEncuesta
from pymongo import MongoClient
# ============================================================
# 🚀 CONVERSACIÓN SEGURA CON AUTOSAVE + REANUDACIÓN AUTOMÁTICA
# ============================================================
# Conexión a MongoDB (ajusta URI según tu entorno)
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "rasa_autosave"
COLLECTION = "autosaves"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
autosave_collection = db[COLLECTION]
class ActionVerificarEstadoConversacion(Action):
    def name(self) -> Text:
        return "action_verificar_estado_conversacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        encuesta_activa = tracker.get_slot("encuesta_activa")
        if encuesta_activa:
            dispatcher.utter_message(response="utter_confirmar_cierre")
            return []
        else:
            dispatcher.utter_message(response="utter_cierre_confirmado")
            return [ConversationPaused()]


class ActionGuardarProgresoConversacion(Action):
    def name(self) -> Text:
        return "action_guardar_progreso_conversacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(response="utter_guardando_progreso")

        # Lógica real de persistencia a través de ActionRegistrarEncuesta
        encuesta_data = {
            "usuario": tracker.sender_id,
            "estado": "incompleta",
            "timestamp": datetime.now().isoformat(),
            "tipo": tracker.get_slot("encuesta_activa"),
            "comentario": tracker.latest_message.get("text", ""),
        }

        try:
            ActionRegistrarEncuesta().registrar_en_base(encuesta_data)
            dispatcher.utter_message(text="✅ Progreso guardado correctamente.")
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ No se pudo guardar el progreso: {str(e)}")

        return [SlotSet("encuesta_activa", True)]


class ActionTerminarConversacionSegura(Action):
    def name(self) -> Text:
        return "action_terminar_conversacion_segura"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        encuesta_activa = tracker.get_slot("encuesta_activa")

        if encuesta_activa:
            dispatcher.utter_message(response="utter_confirmar_cierre")
        else:
            dispatcher.utter_message(response="utter_cierre_confirmado")
            return [ConversationPaused()]
        return []


class ActionReanudarConversacionSegura(Action):
    def name(self) -> Text:
        return "action_reanudar_conversacion_segura"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        # Simula recuperación del estado desde base de datos o tracker store
        encuesta_activa = tracker.get_slot("encuesta_activa")

        if encuesta_activa:
            dispatcher.utter_message(text="🔄 Retomamos tu encuesta o proceso pendiente donde lo dejaste.")
            return [ConversationResumed()]
        else:
            dispatcher.utter_message(text="No había nada pendiente, puedes continuar normalmente.")
        return []
class ActionConfirmarCierreSeguro(Action):
    def name(self):
        return "action_confirmar_cierre_seguro"

    def run(self, dispatcher, tracker, domain):
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(response="utter_confirmar_cierre")
        else:
            dispatcher.utter_message(response="utter_cierre_confirmado")
            return [ConversationPaused()]
        return []


class ActionAutoSaveEncuesta(Action):
    def name(self):
        return "action_autosave_encuesta"

    def run(self, dispatcher, tracker, domain):
        datos = tracker.current_slot_values()
        autosave_collection.update_one(
            {"user_id": tracker.sender_id},
            {"$set": {"slots": datos, "estado": "guardado"}},
            upsert=True
        )
        dispatcher.utter_message(text="Progreso guardado automáticamente 🧠")
        return []


class ActionGuardarAutoSaveMongo(Action):
    def name(self):
        return "action_guardar_autosave_mongo"

    def run(self, dispatcher, tracker, domain):
        data = {"user_id": tracker.sender_id, "slots": tracker.current_slot_values()}
        autosave_collection.update_one({"user_id": tracker.sender_id}, {"$set": data}, upsert=True)
        dispatcher.utter_message(text="Datos guardados en MongoDB 🗄️")
        return []


class ActionCargarAutoSaveMongo(Action):
    def name(self):
        return "action_cargar_autosave_mongo"

    def run(self, dispatcher, tracker, domain):
        registro = autosave_collection.find_one({"user_id": tracker.sender_id})
        if registro and "slots" in registro:
            dispatcher.utter_message(text="Cargando tus datos previos...")
            return [SlotSet(k, v) for k, v in registro["slots"].items()]
        else:
            dispatcher.utter_message(text="No se encontró información guardada previa.")
        return []


class ActionAutoResumeConversacion(Action):
    def name(self):
        return "action_autoresume_conversacion"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="He restaurado tu conversación anterior. Puedes continuar.")
        return [ConversationResumed()]


class ActionResetConversacionSegura(Action):
    def name(self):
        return "action_reset_conversacion_segura"

    def run(self, dispatcher, tracker, domain):
        autosave_collection.delete_one({"user_id": tracker.sender_id})
        dispatcher.utter_message(text="Datos temporales eliminados correctamente. ✅")
        return [SlotSet("encuesta_activa", False), SlotSet("autosave_estado", None)]