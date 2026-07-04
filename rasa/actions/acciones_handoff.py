# ruta: rasa/actions/acciones_handoff.py

from __future__ import annotations

from typing import Any, Dict, List, Text
import logging

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import (
    SlotSet,
    EventType,
    FollowupAction,
)

from .core.llm_engine import run_llm

logger = logging.getLogger(__name__)


# ================================================================
# 🧼 HELPERS
# ================================================================
def _safe_latest_message(tracker: Tracker) -> Dict[str, Any]:
    return tracker.latest_message or {}


def _safe_latest_intent(tracker: Tracker) -> str:
    try:
        return (
            _safe_latest_message(tracker)
            .get("intent", {})
            .get("name", "unknown")
        )
    except Exception:
        return "unknown"


def _safe_sender(tracker: Tracker) -> str:
    return str(getattr(tracker, "sender_id", "") or "anonymous")


def _safe_slot(tracker: Tracker, slot_name: str, default: str = "") -> str:
    value = tracker.get_slot(slot_name)

    if value is None:
        return default

    return str(value).strip()


# ================================================================
# 🧠 RESUMEN PARA AGENTE HUMANO
# ================================================================
def _build_handoff_base_text(tracker: Tracker) -> str:
    """
    Construye un contexto seguro para generar
    un resumen del caso destinado al agente humano.
    """

    motivo = _safe_slot(
        tracker,
        "motivo_soporte",
        "soporte general",
    )

    tipo_soporte = _safe_slot(
        tracker,
        "tipo_soporte",
        "interno",
    )

    ultimo_intent = _safe_latest_intent(tracker)

    
    raw_text = _safe_latest_message(tracker).get("text")
    ultimo_mensaje = str(raw_text).strip() if raw_text else "Sin texto disponible (Evento o Multimedia)"

    return (
        "Genera un resumen breve y claro del caso "
        "para un agente humano de soporte.\n\n"
        f"- Tipo de soporte: {tipo_soporte}\n"
        f"- Motivo principal: {motivo}\n"
        f"- Último intent detectado: {ultimo_intent}\n"
        f"- Último mensaje del usuario: "
        f"\"{ultimo_mensaje}\"\n\n"
        "No incluyas correos, teléfonos, documentos, "
        "tokens, URLs ni datos sensibles. "
        "Resume únicamente el problema reportado "
        "y el contexto de la conversación."
    )


def _generate_handoff_summary(tracker: Tracker) -> str:
    """
    Genera un resumen interno del caso para el agente humano.

    Este resumen NO se envía al usuario.
    Forma parte de la lógica de negocio del handoff, por lo que
    permanece utilizando run_llm() directamente.

    Se incorpora un contexto explícito para mantener consistencia
    con la nueva arquitectura basada en flujos.
    """

    texto_base = _build_handoff_base_text(tracker)

    contexto_llm = {
        "flujo": "handoff",
        "tipo": "resumen_agente",
    }

    try:

        resumen = run_llm(
            prompt=texto_base,
            tracker=tracker,
            context=contexto_llm,
            fallback="",
        )

        if isinstance(resumen, str):
            resumen = resumen.strip()

            if resumen:
                return resumen

    except Exception:

        logger.exception(
            "[HANDOFF_LLM_ERROR] "
            f"user={_safe_sender(tracker)}"
        )

    return ""

# ================================================================
# 👤 OFRECER HUMANO
# ================================================================
class ActionOfrecerHumano(Action):

    def name(self) -> Text:
        return "action_ofrecer_humano"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,  
    ) -> List[EventType]:

        dispatcher.utter_message(
            response="utter_ofrecer_humano"
        )

        return []


# ================================================================
# ❌ CANCELAR HANDOFF
# ================================================================
class ActionHandoffCancelar(Action):

    def name(self) -> Text:
        return "action_handoff_cancelar"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        dispatcher.utter_message(
            response="utter_derivacion_cancelada"
        )

        return [
            SlotSet("derivacion_humano", False)
        ]


# ================================================================
# ✅ CONFIRMAR HANDOFF
# ================================================================
class ActionDerivarHumanoConfirmada(Action):

    def name(self) -> Text:
        return "action_derivar_humano_confirmada"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        dispatcher.utter_message(
            response="utter_derivar_humano_en_progreso"
        )

        return [
            FollowupAction(
                "action_derivar_y_registrar_humano"
            )
        ]


# ================================================================
# ❌ CANCELAR DERIVACIÓN
# ================================================================
class ActionCancelarDerivacion(Action):

    def name(self) -> Text:
        return "action_cancelar_derivacion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        dispatcher.utter_message(
            response="utter_derivacion_cancelada"
        )

        return [
            SlotSet("derivacion_humano", False)
        ]


# ================================================================
# 🚀 DERIVAR Y REGISTRAR
# ================================================================
class ActionDerivarYRegistrarHumano(Action):

    def name(self) -> Text:
        return "action_derivar_y_registrar_humano"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        sender_id = _safe_sender(tracker)

        dispatcher.utter_message(
            response="utter_derivando_humano"
        )

        dispatcher.utter_message(
            response="utter_handoff_en_cola"
        )

        try:

            resumen = _generate_handoff_summary(
                tracker
            )

            if resumen:

                logger.info(
                    "[HANDOFF_RESUMEN] "
                    f"user={sender_id} "
                    f"intent={_safe_latest_intent(tracker)} "
                    f"summary={resumen}"
                )

        except Exception:

            logger.exception(
                "[HANDOFF_SUMMARY_ERROR] "
                f"user={sender_id}"
            )

        return [
            SlotSet(
                "derivacion_humano",
                True,
            ),
            SlotSet(
                "proceso_activo",
                "soporte_humano",
            ),
        ]


# ================================================================
# ⏳ EN COLA
# ================================================================
class ActionHandoffEnCola(Action):

    def name(self) -> Text:
        return "action_handoff_en_cola"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        dispatcher.utter_message(
            response="utter_handoff_en_cola"
        )

        return []