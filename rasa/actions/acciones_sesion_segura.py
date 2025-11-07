# rasa/actions/acciones_seguridad.py
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from pymongo import MongoClient
import datetime

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "rasa_autosave"
COLLECTION = "seguridad_autosave"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION]


class ActionNotificarDesconexion(Action):
    def name(self):
        return "action_notificar_desconexion"

    def run(self, dispatcher, tracker, domain):
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


class ActionNotificarInactividad(Action):
    def name(self):
        return "action_notificar_inactividad"

    def run(self, dispatcher, tracker, domain):
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


class ActionNotificarReconexion(Action):
    def name(self):
        return "action_notificar_reconexion"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(response="utter_notificar_reconexion")
        registro = collection.find_one({"user_id": tracker.sender_id})
        if registro and "slots" in registro:
            return [SlotSet(k, v) for k, v in registro["slots"].items()]
        return []


class ActionGuardarEstadoSeguridad(Action):
    def name(self):
        return "action_guardar_estado_seguridad"

    def run(self, dispatcher, tracker, domain):
        data = {
            "user_id": tracker.sender_id,
            "slots": tracker.current_slot_values(),
            "timestamp": datetime.datetime.utcnow(),
            "evento": tracker.get_slot("evento_seguridad"),
        }
        collection.update_one({"user_id": tracker.sender_id}, {"$set": data}, upsert=True)
        dispatcher.utter_message(text="💾 Estado de seguridad guardado.")
        return []


class ActionRecuperarEstadoSeguridad(Action):
    def name(self):
        return "action_recuperar_estado_seguridad"

    def run(self, dispatcher, tracker, domain):
        registro = collection.find_one({"user_id": tracker.sender_id})
        if registro and "slots" in registro:
            dispatcher.utter_message(text="🔄 Restaurando sesión guardada...")
            return [SlotSet(k, v) for k, v in registro["slots"].items()]
        dispatcher.utter_message(text="No se encontró sesión guardada previa.")
        return []
