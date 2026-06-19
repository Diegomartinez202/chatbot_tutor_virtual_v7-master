# ruta: rasa/actions/acciones_conversacion_segura.py
from __future__ import annotations

from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    ConversationPaused,
    ConversationResumed,
    EventType,
)


# ================================================================
# 🧠 MOCK PERSISTENCE LAYER (TEMPORAL)
# ================================================================

_INMEM_AUTOSAVE: Dict[str, Dict[str, Any]] = {}


def _sender_id(tracker: Tracker) -> str:
    return tracker.sender_id or "anon"


# ================================================================
# 🚦 ACTIONS (RASA STATE MACHINE LAYER)
# ================================================================

class ActionConfirmarCierreSeguro(Action):

    def name(self) -> Text:
        return "action_confirmar_cierre_seguro"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(response="utter_confirmar_cierre_seguro")
            return []

        dispatcher.utter_message(response="utter_cierre_confirmado_seguro")
        return [ConversationPaused()]


class ActionCargarAutosaveMongo(Action):

    def name(self) -> Text:
        return "action_cargar_autosave_mongo"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        sid = _sender_id(tracker)
        data = dict(_INMEM_AUTOSAVE.get(sid) or {})  # MEJORA: Copia segura de diccionario

        events: List[EventType] = [
            SlotSet(k, v) for k, v in data.items()
        ]

        if data:
            dispatcher.utter_message(text="📂 He cargado tu progreso guardado.")
            dispatcher.utter_message(response="utter_reanudar_conversacion")
        else:
            dispatcher.utter_message(
                text="ℹ️ No encontré progreso previo para reanudar."
            )

        return events


class ActionAutoresumeConversacion(Action):

    def name(self) -> Text:
        return "action_autoresume_conversacion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        encuesta_activa = bool(
            tracker.get_slot("encuesta_activa")
        )

        nombre = (
            tracker.get_slot("nombre")
            or "usuario"
        )

        if encuesta_activa:

            dispatcher.utter_message(
                text=f"👋 Hola {nombre}, encontramos una sesión pendiente."
            )

            dispatcher.utter_message(
                response="utter_reanudar_conversacion"
            )

            return [
                SlotSet("reanudar_pendiente", False),
                ConversationResumed()
            ]

        dispatcher.utter_message(
            text="No hay procesos pendientes."
        )

        return []


class ActionResetConversacionSegura(Action):

    def name(self) -> Text:
        return "action_reset_conversacion_segura"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        sid = _sender_id(tracker)
        _INMEM_AUTOSAVE.pop(sid, None)

        dispatcher.utter_message(
            text="🧹 Estado de conversación segura limpiado."
        )

        # MEJORA: Limpieza quirúrgica de los slots de control de encuestas en el reset seguro
        return [
            SlotSet("encuesta_activa", False),
            SlotSet("encuesta_incompleta", False),
            SlotSet("autosave_estado", None),
            SlotSet("encuesta_tipo", None),
            ConversationPaused(),
        ]