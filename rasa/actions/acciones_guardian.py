# ruta: rasa/actions/acciones_guardian.py

from __future__ import annotations

import os
import datetime
from typing import Any, Dict, List, Text
import logging
from rasa_sdk.types import DomainDict
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    FollowupAction,
    ConversationPaused,
    ConversationResumed,
    EventType,
)
from utils.mongo_autosave import guardar_autosave, log_event
from utils.mongo_semantic_memory import collection
from utils.guardian_client import GuardianClient
from .core.llm_engine import run_llm

logger = logging.getLogger(__name__)

from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "chatbot_tutor_virtual")
_client = MongoClient(MONGO_URI)
_db = _client[MONGO_DB]
_autos = _db[os.getenv("MONGO_AUTOSAVE_COLLECTION", "autosaves")]

def _log(usuario, evento, estado, detalle=None):
    from utils.mongo_autosave import log_event
    log_event(usuario, evento, estado, detalle)

GUARDIAN_URL = os.getenv(
    "GUARDIAN_URL",
    "http://autosave-guardian:8080"
)

GUARDIAN_USER = os.getenv(
    "GUARDIAN_USER",
    "admin"
)

GUARDIAN_PASSWORD = os.getenv("GUARDIAN_PASSWORD")

if not GUARDIAN_PASSWORD:
    raise RuntimeError(
        "GUARDIAN_PASSWORD no configurado"
    )

MAX_INTENTOS_FORM = 3


# ================================================================
# 🧼 HELPERS
# ================================================================
def _safe_latest_intent(tracker: Tracker) -> str:
    try:
        return (
            (tracker.latest_message or {})
            .get("intent", {})
            .get("name", "unknown")
        )
    except Exception:
        return "unknown"


def _safe_sender(tracker: Tracker) -> str:
    return str(getattr(tracker, "sender_id", "") or "anonymous")


# ================================================================
# 💾 AUTOSAVE SNAPSHOT
# ================================================================
class ActionAutosaveSnapshot(Action):

    def name(self) -> Text:
        return "action_autosave_snapshot"

    # ==========================================================
    # HELPER
    # ==========================================================
    def _build_guardian_snapshot_llm_request(
        self,
        events_count: int,
    ) -> Dict[str, Any]:
        """
        Construye la solicitud que será procesada por
        ActionHandleWithLLM.

        Esta acción NO genera lenguaje natural directamente.
        Solo prepara el contexto para el orquestador central.
        """

        return {
            "instruction": (
                "Se guardó un snapshot automático de la sesión para "
                "poder retomarla más adelante o para que un asesor "
                "humano tenga contexto del caso. "
                "Aclara que no se almacenan contraseñas ni información "
                "financiera sensible."
            ),
            "context": {
                "flujo": "guardian_autosave",
                "events_count": events_count,
            },

            "fallback": (
                "✅ Se guardó una copia de seguridad de la sesión."
            ),
            "context": {

                "flujo": "guardian_encuesta",
            },
            "fallback": (
                "✅ Registro de satisfacción guardado correctamente."
            ),

        }

    # ==========================================================
    # RUN
    # ==========================================================
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        sender_id = _safe_sender(tracker)

        gc = None
        ok = False

        data = {
            "latest_intent": _safe_latest_intent(tracker),
            "slots": tracker.current_slot_values() or {},
            "events_count": len(tracker.events or []),
        }

        # --------------------------------------------------------
        # Crear cliente Guardian
        # --------------------------------------------------------
        try:

            logger.info(
                "[GUARDIAN CONFIG] url=%s user=%s",
                GUARDIAN_URL,
                GUARDIAN_USER,
            )

            gc = GuardianClient(
                base_url=GUARDIAN_URL,
                username=GUARDIAN_USER,
                password=GUARDIAN_PASSWORD,
                timeout=4.0,
                max_retries=2,
            )

            logger.info(
                "[GUARDIAN_AUTOSAVE] user=%s intent=%s events=%s",
                sender_id,
                data["latest_intent"],
                data["events_count"],
            )

            ok = gc.autosave_create(
                sender_id=sender_id,
                data=data,
            )

        except Exception as e:

            logger.exception(
                "[GUARDIAN_CONNECTION_ERROR] user=%s error=%s",
                sender_id,
                e,
            )

            dispatcher.utter_message(
                text=(
                    "⚠️ No fue posible guardar el snapshot "
                    "en este momento."
                )
            )

            return []

        # --------------------------------------------------------
        # Auditoría (NO bloqueante)
        # --------------------------------------------------------
        try:

            if gc is not None:

                gc.log_event(
                    "action_autosave_snapshot_called",
                    {
                        "sender_id": sender_id,
                        "latest_intent": data["latest_intent"],
                    },
                )

        except Exception as e:

            logger.warning(
                "[GUARDIAN_LOG_EVENT_ERROR] user=%s error=%s",
                sender_id,
                e,
            )

        # --------------------------------------------------------
        # Snapshot guardado correctamente
        # --------------------------------------------------------
        if ok:

            return [

                SlotSet(
                    "llm_request",
                    self._build_guardian_snapshot_llm_request(
                        data["events_count"]
                    ),
                ),

                FollowupAction(
                    "action_handle_with_llm"
                ),
            ]

        # --------------------------------------------------------
        # Error guardando snapshot
        # --------------------------------------------------------
        logger.warning(
            "[GUARDIAN_AUTOSAVE_FAILED] user=%s",
            sender_id,
        )

        dispatcher.utter_message(
            text=(
                "⚠️ No fue posible guardar el snapshot "
                "en este momento."
            )
        )

        return []

class ActionGuardianGuardarProgreso(Action):
    def name(self) -> Text:
        return "action_guardian_guardar_progreso"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        usuario = tracker.sender_id
        tiene_encuesta = tracker.get_slot("encuesta_activa")
        
        # 1. Preparar el payload
        payload = {
            "user_id": usuario,
            "slots": tracker.current_slot_values(),
            "estado": "guardado",
            "updated_at": datetime.datetime.utcnow(),
        }

        # 2. Intentar guardar en Mongo
        try:
            _autos.update_one(
                {"user_id": usuario},
                {"$set": payload},
                upsert=True,
            )
            _log(usuario, "guardian_guardar_progreso", "ok", {"encuesta_previa": tiene_encuesta})
        except Exception as e:
            _log(usuario, "guardian_guardar_progreso", "error", {"error": str(e)})
            dispatcher.utter_message(text="⚠️ No fue posible guardar el progreso en este momento.")
            return []

        # 3. Lógica de comunicación (Manteniendo el flujo sin ser agresivo)
        if tiene_encuesta:
            dispatcher.utter_message(
                text="✅ Progreso guardado. Veo que tienes una encuesta pendiente, ¿te gustaría completarla ahora o prefieres continuar más tarde?"
            )
        else:
            # Mensaje estándar de confirmación
            dispatcher.utter_message(text="✅ Progreso guardado correctamente.")

        # Retornamos el estado. No sobreescribimos encuesta_activa, 
        # mantenemos el valor que ya tenga el tracker.
        return []

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

    # ==========================================================
    # HELPER
    # ==========================================================

    def _build_llm_request(
        self,
        intent: str | None,
    ) -> Dict[str, Any]:

        return {

            "instruction": (
                "Informa al usuario que el registro de satisfacción "
                "fue almacenado correctamente y que el autosave quedó "
                "actualizado para conservar el contexto de la conversación. "
                "Agradece brevemente su colaboración."
            ),

            "context": {
                "flujo": "guardian_encuesta",
                "ultimo_intent": intent,
            },

            "fallback": (
                "✅ Registro de satisfacción guardado correctamente."
            ),
        }

    # ==========================================================
    # RUN
    # ==========================================================

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

            _log(
                tracker.sender_id,
                "registrar_encuesta",
                "ok",
                {
                    "intent": data["ultimo_intent"],
                },
            )

            return [

                SlotSet(
                    "llm_request",
                    self._build_llm_request(
                        data["ultimo_intent"],
                    ),
                ),

                FollowupAction(
                    "action_handle_with_llm"
                ),

            ]

        except Exception:

            logger.exception(
                "[GUARDIAN_SURVEY] error guardando encuesta"
            )

            dispatcher.utter_message(
                text="⚠️ No fue posible registrar la encuesta."
            )

            return []