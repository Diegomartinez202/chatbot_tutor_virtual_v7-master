# ruta: rasa/actions/acciones_guardian.py

from __future__ import annotations

import os
from typing import Any, Dict, List, Text
import logging

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType
from utils.mongo_semantic_memory import collection
from utils.guardian_client import GuardianClient
from .core.llm_engine import run_llm

logger = logging.getLogger(__name__)

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