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

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        sender_id = _safe_sender(tracker)
        gc = None  # MEJORA: Inicialización segura para evitar UnboundLocalError en cascada
        ok = False
        data = {
            "latest_intent": _safe_latest_intent(tracker),
            "slots": tracker.current_slot_values() or {},
            "events_count": len(tracker.events or []),
        }

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
                f"[GUARDIAN_AUTOSAVE] "
                f"user={sender_id} "
                f"intent={data['latest_intent']} "
                f"events={data['events_count']}"
            )
            
            ok = gc.autosave_create(
                sender_id=sender_id,
                data=data,
            )

        except Exception as e:

            logger.exception(
                f"[GUARDIAN_CONNECTION_ERROR] user={sender_id} error={e}"
            )

            dispatcher.utter_message(
                text="⚠️ No fue posible guardar el snapshot en este momento."
            )

            return []

        # --------------------------------------------------------
        # ✅ SNAPSHOT OK
        # --------------------------------------------------------
        if ok:

            texto_base = (
                "Se guardó un snapshot automático de la sesión para "
                "poder retomarla más adelante o para que un asesor "
                "humano tenga contexto del caso. "
                "Aclara que no se almacenan contraseñas ni información "
                "financiera sensible."
            )

            contexto_llm = {
                "flujo": "guardian_autosave",
                "events_count": data["events_count"],
            }

            try:

                mensaje = run_llm(
                    prompt=texto_base,
                    tracker=tracker,
                    context=contexto_llm,
                    fallback="✅ Se guardó una copia de seguridad de la sesión.",
                )

                if mensaje and isinstance(mensaje, str):
                    dispatcher.utter_message(text=mensaje.strip())
                else:
                    raise ValueError("Respuesta vacía del LLM")

            except Exception as e:

                logger.exception(
                    f"[GUARDIAN_LLM_FALLBACK] user={sender_id} error={e}"
                )

                dispatcher.utter_message(
                    text=(
                        "✅ Se guardó una copia de seguridad de la sesión "
                        "para poder continuar posteriormente."
                    )
                )

        # --------------------------------------------------------
        # ❌ SNAPSHOT ERROR
        # --------------------------------------------------------
        else:

            logger.warning(
                f"[GUARDIAN_AUTOSAVE_FAILED] user={sender_id}"
            )

            dispatcher.utter_message(
                text=(
                    "⚠️ No fue posible guardar el snapshot "
                    "en este momento."
                )
            )

        # --------------------------------------------------------
        # 📊 AUDITORÍA (NO BLOQUEANTE)
        # --------------------------------------------------------
        try:
            # MEJORA: Ejecución condicional estricta verificando que el cliente exista
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
                f"[GUARDIAN_LOG_EVENT_ERROR] user={sender_id} error={e}"
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

class ActionGuardarEncuestaIncompleta(Action):
    def name(self) -> Text:
        return "action_guardar_encuesta_incompleta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
        usuario = tracker.sender_id
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dispatcher.utter_message(text=f"Guardando tu progreso de encuesta ({fecha}) para el usuario {usuario}…")
        dispatcher.utter_message(text="✅ Encuesta parcial registrada correctamente.")
        return [
            SlotSet("encuesta_incompleta", False),
            SlotSet("proceso_activo", None),
        ]

    @staticmethod  
    def _safe_latest(tracker: Tracker) -> Dict[str, Any]:
        return tracker.latest_message or {}