# ruta: rasa/actions/acciones_seguridad_guardian.py
from __future__ import annotations

import os
import datetime
from typing import Any, Dict, List, Text, Optional

from pymongo import MongoClient
from rasa_sdk import Action, Tracker
from rasa_sdk.events import (
    SlotSet,
    ConversationPaused,
    ConversationResumed,
    EventType,
)
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

from rasa.utils.mongo_autosave import guardar_autosave, log_event
from rasa.utils.guardian_client import GuardianClient
import logging

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "chatbot_tutor_virtual")
AUTOSAVE_COLLECTION = os.getenv("MONGO_AUTOSAVE_COLLECTION", "autosaves")

_client = MongoClient(MONGO_URI)
_db = _client[MONGO_DB]
_autos = _db[AUTOSAVE_COLLECTION]


def _log(
    usuario: str,
    evento: str,
    estado: str,
    detalle: Optional[Dict[str, Any]] = None,  # MEJORA: Tipado robusto compatible con runtimes Python 3.9+
):
    log_event(usuario, evento, estado, detalle)


class ActionGuardianGuardarProgreso(Action):

    def name(self) -> Text:
        return "action_guardian_guardar_progreso"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        dispatcher.utter_message(response="utter_guardando_progreso")

        usuario = tracker.sender_id

        payload = {
            "user_id": usuario,
            "slots": tracker.current_slot_values(),
            "estado": "guardado",
            "updated_at": datetime.datetime.utcnow(),
        }

        try:
            _autos.update_one(
                {"user_id": usuario},
                {"$set": payload},
                upsert=True,
            )

        except Exception:
            _log(
                usuario,
                "guardian_guardar_progreso",
                "error",
            )

            dispatcher.utter_message(
                text="⚠️ No fue posible guardar el progreso en este momento."
            )
            return []

        _log(
            usuario,
            "guardian_guardar_progreso",
            "ok",
            {"slots": len(payload["slots"] or {})},
        )

        dispatcher.utter_message(
            text="✅ Progreso guardado correctamente."
        )

        return [
            SlotSet("encuesta_activa", True)
        ]


class ActionGuardianCargarProgreso(Action):

    def name(self) -> Text:
        return "action_guardian_cargar_progreso"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        usuario = tracker.sender_id

        try:
            doc = _autos.find_one({"user_id": usuario})
        except Exception:
            doc = None

        if doc and "slots" in doc:

            _log(
                usuario,
                "guardian_cargar_progreso",
                "ok",
                {"existe": True},
            )

            dispatcher.utter_message(
                text="🔄 Cargando tu progreso guardado…"
            )

            return [
                SlotSet(k, v)
                for k, v in (doc.get("slots") or {}).items()
            ]

        _log(
            usuario,
            "guardian_cargar_progreso",
            "ok",
            {"existe": False},
        )

        dispatcher.utter_message(
            text="No se encontró información previa."
        )

        return []


class ActionGuardianPausar(Action):
    def name(self) -> Text:
        return "action_guardian_pausar"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        usuario = tracker.sender_id
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(response="utter_confirmar_cierre")
            _log(usuario, "guardian_pausar_requiere_confirmacion", "ok")
            return []
        dispatcher.utter_message(response="utter_cierre_confirmado")
        _log(usuario, "guardian_pausar", "ok")
        return [ConversationPaused()]


class ActionGuardianReanudar(Action):
    def name(self) -> Text:
        return "action_guardian_reanudar"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        usuario = tracker.sender_id
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(text="🔁 Retomamos donde quedaste.")
            _log(usuario, "guardian_reanudar", "ok", {"encuesta_activa": True})
            return [ConversationResumed()]
        dispatcher.utter_message(text="No había nada pendiente, puedes continuar.")
        _log(usuario, "guardian_reanudar", "ok", {"encuesta_activa": False})
        return []


class ActionGuardianReset(Action):

    def name(self) -> Text:
        return "action_guardian_reset"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        usuario = tracker.sender_id

        try:
            _autos.delete_one({"user_id": usuario})
        except Exception:
            logger.exception(
                "[GUARDIAN_RESET] error eliminando autosave"
            )

        _log(
            usuario,
            "guardian_reset",
            "ok",
        )

        dispatcher.utter_message(
            text="🧹 Datos temporales eliminados."
        )

        return [
            SlotSet("encuesta_activa", False),
            SlotSet("autosave_estado", None),
        ]


class ActionRegistrarEncuestaGuardian(Action):

    def name(self) -> str:
        return "action_registrar_encuesta_guardian"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        latest = tracker.latest_message or {}

        data = {
            "usuario": tracker.sender_id,
            "ultimo_intent": (
                latest.get("intent", {}) or {}
            ).get("name"),
            "texto": latest.get("text"),
            "slots": tracker.current_slot_values(),
        }

        try:
            guardar_autosave(
                tracker.sender_id,
                data,
            )

            dispatcher.utter_message(
                text="✅ Registro de satisfacción guardado y autosave completado."
            )

            _log(
                tracker.sender_id,
                "registrar_encuesta",
                "ok",
                {"intent": data["ultimo_intent"]},
            )

        except Exception:
            logger.exception(
                "[GUARDIAN_SURVEY] error guardando encuesta"
            )

            dispatcher.utter_message(
                text="⚠️ No fue posible registrar la encuesta."
            )

        return []


class ActionGuardarAutosave(Action):

    def name(self) -> Text:
        return "action_guardar_autosave"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  # MEJORA: Ajustado de Dict a DomainDict para homogeneizar la arquitectura
    ) -> List[EventType]:

        try:
            client = GuardianClient(
                base_url=os.getenv(
                    "GUARDIAN_URL",
                    "http://autosave-guardian:8080"
                ),
                username=os.getenv(
                "GUARDIAN_USER",
                "admin"
                ),
                password=os.getenv(
                    "GUARDIAN_PASSWORD",
                    ""
                ),
            )

        except Exception:
            logger.exception(
                "[GUARDIAN_AUTOSAVE] error creando cliente"
            )
            client = None

        if not client:
            dispatcher.utter_message(
                text="Autosave temporalmente no disponible."
            )
            return []

        latest = tracker.latest_message or {}

        payload = {
            "latest_intent": (
                latest.get("intent", {}) or {}
            ).get("name"),
            "latest_text": latest.get("text"),
            "slots": tracker.current_slot_values(),
        }

        try:
            ok = client.autosave_create(
                tracker.sender_id,
                payload,
            )

        except Exception:
            logger.exception(
                "[GUARDIAN_AUTOSAVE] error creando autosave"
            )
            ok = False

        if ok:
            dispatcher.utter_message(
                response="utter_guardando_progreso"
            )

            return [
                SlotSet("encuesta_activa", True)
            ]

        return []

    @staticmethod  # MEJORA: Decorador explícito para evitar problemas de contexto en tiempo de ejecución
    def _safe_latest(tracker: Tracker) -> Dict[str, Any]:
        return tracker.latest_message or {}