# ruta: rasa/actions/acciones_seguridad.py
from __future__ import annotations

import os
import datetime
from typing import Any, Text, Dict, List
import logging

from pymongo import MongoClient
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import (
    SlotSet,
    FollowupAction,
    ConversationPaused,
    ConversationResumed,
    EventType,
)
from .core.llm_engine import run_llm

logger = logging.getLogger(__name__)

# MEJORA: Extracción parametrizada mediante variables de entorno para Docker Compose
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "rasa_autosave")
COLLECTION = os.getenv("MONGO_SECURITY_COLLECTION", "seguridad_autosave")

try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=3000,
    )
    db = client[DB_NAME]
    collection = db[COLLECTION]
except Exception:
    logger.exception(
        "[SECURITY_SESSION] Mongo unavailable en la dirección proporcionada"
    )
    collection = None


class ActionNotificarDesconexion(Action):

    def name(self) -> Text:
        return "action_notificar_desconexion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Firma tipada estandarizada
    ) -> List[EventType]:

        dispatcher.utter_message(
            response="utter_notificar_desconexion"
        )

        user_id = tracker.sender_id

        estado = {
            "user_id": user_id,
            "timestamp": datetime.datetime.utcnow(),
            "slots": tracker.current_slot_values(),
            "evento": "desconexion",
        }

        if collection is not None:
            try:
                collection.update_one(
                    {"user_id": user_id},
                    {"$set": estado},
                    upsert=True,
                )
            except Exception:
                logger.exception(
                    "[SECURITY_SESSION] disconnect save failed"
                )

        return [
            SlotSet(
                "evento_seguridad",
                "desconexion",
            )
        ]


class ActionNotificarInactividad(Action):

    def name(self) -> Text:
        return "action_notificar_inactividad"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Estandarización de firma de Rasa SDK
    ) -> List[EventType]:

        dispatcher.utter_message(
            response="utter_notificar_inactividad"
        )

        user_id = tracker.sender_id

        estado = {
            "user_id": user_id,
            "timestamp": datetime.datetime.utcnow(),
            "slots": tracker.current_slot_values(),
            "evento": "inactividad",
        }

        if collection is not None:  # MEJORA: Verificación explícita de seguridad
            try:
                collection.update_one(
                    {"user_id": user_id},
                    {"$set": estado},
                    upsert=True,
                )
            except Exception:
                logger.exception(
                    "[SECURITY_SESSION] inactivity save failed"
                )

        return [
            SlotSet(
                "evento_seguridad",
                "inactividad",
            )
        ]


class ActionNotificarReconexion(Action):

    def name(self) -> Text:
        return "action_notificar_reconexion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        dispatcher.utter_message(
            response="utter_notificar_reconexion"
        )

        registro = None

        if collection is not None:
            try:
                registro = collection.find_one(
                    {
                        "user_id": tracker.sender_id
                    }
                )
            except Exception:
                logger.exception(
                    "[SECURITY_SESSION] reconnect lookup failed"
                )

        events: List[EventType] = []

        # --------------------------------------------------------
        # Restaurar estado previamente guardado
        # --------------------------------------------------------
        if registro and "slots" in registro:

            for k, v in registro["slots"].items():
                events.append(
                    SlotSet(k, v)
                )

            try:

                evento_prev = registro.get(
                    "evento",
                    "desconocido",
                )

                # ------------------------------------------------
                # Delegar únicamente la generación del mensaje
                # al ActionHandleWithLLM
                # ------------------------------------------------

                events.append(

                    SlotSet(
                        "llm_request",
                        {
                            "instruction": (
                                "El usuario se ha reconectado a la conversación. "
                                f"Había un evento previo registrado: {evento_prev}. "
                                "Genera un mensaje breve, amable y claro indicando "
                                "que su sesión fue restaurada correctamente y que "
                                "puede continuar donde la dejó. "
                                "No menciones detalles de los slots ni datos sensibles."
                            ),

                            "context": {
                                "flujo": "seguridad_reconexion",
                                "evento_prev": evento_prev,
                                "tiene_sesion_guardada": True,
                            },

                            "fallback": (
                                "🔄 Tu sesión anterior fue restaurada correctamente."
                            ),
                        },
                    )

                )

                events.append(

                    FollowupAction(
                        "action_handle_with_llm"
                    )

                )

            except Exception:

                logger.exception(
                    "[SECURITY_SESSION] reconnect llm preparation failed"
                )

                dispatcher.utter_message(
                    text=(
                        "🔄 Tu sesión anterior fue restaurada correctamente."
                    )
                )

            return events

        return events


class ActionGuardarEstadoSeguridad(Action):  # NOTA: Mantiene mapeo idéntico al name()

    def name(self) -> Text:
        return "action_guardar_estado_seguridad"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        data = {
            "user_id": tracker.sender_id,
            "slots": tracker.current_slot_values(),
            "timestamp": datetime.datetime.utcnow(),
            "evento": tracker.get_slot(
                "evento_seguridad"
            ),
        }

        if collection is not None:
            try:
                collection.update_one(
                    {"user_id": tracker.sender_id},
                    {"$set": data},
                    upsert=True,
                )
            except Exception:
                logger.exception(
                    "[SECURITY_SESSION] save state failed"
                )

        dispatcher.utter_message(
            text="💾 Estado de seguridad guardado."
        )

        return []


class ActionRecuperarEstadoSeguridad(Action):

    def name(self) -> Text:
        return "action_recuperar_estado_seguridad"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        registro = None

        # --------------------------------------------------------
        # Recuperar sesión almacenada
        # --------------------------------------------------------
        if collection is not None:
            try:
                registro = collection.find_one(
                    {
                        "user_id": tracker.sender_id
                    }
                )
            except Exception:
                logger.exception(
                    "[SECURITY_SESSION] restore failed"
                )

        # --------------------------------------------------------
        # Restaurar estado encontrado
        # --------------------------------------------------------
        if registro and "slots" in registro:

            dispatcher.utter_message(
                text="🔄 Restaurando sesión guardada..."
            )

            events: List[EventType] = [

                SlotSet(k, v)

                for k, v in registro["slots"].items()

            ]

            try:

                evento_prev = registro.get(
                    "evento",
                    "desconocido",
                )

                # ------------------------------------------------
                # Delegar únicamente la generación del mensaje
                # al orquestador LLM
                # ------------------------------------------------

                events.append(

                    SlotSet(
                        "llm_request",
                        {
                            "instruction": (
                                "Se ha recuperado un estado de seguridad "
                                "previo para el usuario. "
                                f"El último evento registrado fue: "
                                f"{evento_prev}. "
                                "Genera un mensaje corto, claro y amable "
                                "indicando que la sesión fue restaurada "
                                "correctamente y que el usuario puede "
                                "continuar donde quedó. "
                                "No menciones datos sensibles."
                            ),

                            "context": {
                                "flujo": "seguridad_recuperar_estado",
                                "evento_prev": evento_prev,
                                "tiene_sesion_guardada": True,
                            },

                            "fallback": (
                                "🔄 Tu sesión fue restaurada correctamente. "
                                "Puedes continuar donde quedaste."
                            ),
                        },
                    )

                )

                events.append(

                    FollowupAction(
                        "action_handle_with_llm"
                    )

                )

            except Exception:

                logger.exception(
                    "[SECURITY_SESSION] llm restore preparation failed"
                )

                dispatcher.utter_message(
                    text=(
                        "🔄 Tu sesión fue restaurada correctamente. "
                        "Puedes continuar donde quedaste."
                    )
                )

            return events

        # --------------------------------------------------------
        # No existe sesión previa
        # --------------------------------------------------------
        dispatcher.utter_message(
            text="No se encontró una sesión guardada previa."
        )

        return []

# --- CLASES DE PERSISTENCIA DE AUTOSAVE ---

class ActionCargarAutosaveMongo(Action):
    def name(self) -> Text:
        return "action_cargar_autosave_mongo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        user_id = tracker.sender_id
        registro = None
        
        if collection is not None:
            try:
                registro = collection.find_one({"user_id": user_id})
            except Exception:
                logger.exception("[AUTOSAVE_LOAD] Error consultando Mongo")

        if registro and "slots" in registro:
            dispatcher.utter_message(text="📂 He cargado tu progreso guardado.")
            dispatcher.utter_message(response="utter_reanudar_conversacion")
            return [SlotSet(k, v) for k, v in registro["slots"].items()]
        
        dispatcher.utter_message(text="ℹ️ No encontré progreso previo para reanudar.")
        return []

class ActionAutoresumeConversacion(Action):
    def name(self) -> Text:
        return "action_autoresume_conversacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        nombre = tracker.get_slot("nombre") or "usuario"
        
        # Si la encuesta está activa, intentamos reanudar
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(text=f"👋 Hola {nombre}, encontramos una sesión pendiente.")
            dispatcher.utter_message(response="utter_reanudar_conversacion")
            return [SlotSet("reanudar_pendiente", False), ConversationResumed()]
        
        dispatcher.utter_message(text="No hay procesos pendientes.")
        return []

