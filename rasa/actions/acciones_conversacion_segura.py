# ruta: rasa/actions/acciones_conversacion_segura.py
from __future__ import annotations
from typing import Any, Dict, List, Text, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ConversationPaused, ConversationResumed

# ------- Helpers mínimos (simulan persistencia) -------
# En producción, reemplaza este "store" por Mongo/Redis.
_INMEM_AUTOSAVE: Dict[str, Dict[str, Any]] = {}

def _sender_id(tracker: Tracker) -> str:
    return tracker.sender_id or "anon"

# --------------- Acciones -----------------------------

class ActionConfirmarCierreSeguro(Action):
    def name(self) -> Text:
        return "action_confirmar_cierre_seguro"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List:
        encuesta_activa = bool(tracker.get_slot("encuesta_activa"))
        if encuesta_activa:
            dispatcher.utter_message(response="utter_confirmar_cierre")
            return []
        # Si no hay encuesta activa, confirmamos de una
        dispatcher.utter_message(response="utter_cierre_confirmado")
        return [ConversationPaused()]

class ActionAutosaveEncuesta(Action):
    def name(self) -> Text:
        return "action_autosave_encuesta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List:
        # Marca que hay algo que guardar (si no lo estaba ya)
        dispatcher.utter_message(text="💾 Guardando tu progreso antes de cerrar...")
        return [SlotSet("encuesta_activa", True)]

class ActionGuardarAutosaveMongo(Action):
    """Simula guardar en Mongo. Cambia por tu integración real."""
    def name(self) -> Text:
        return "action_guardar_autosave_mongo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List:
        sid = _sender_id(tracker)
        data = {
            "encuesta_activa": True,
            "encuesta_tipo": tracker.get_slot("encuesta_tipo"),
            "autosave_estado": tracker.get_slot("autosave_estado"),
        }
        _INMEM_AUTOSAVE[sid] = data
        dispatcher.utter_message(text="✅ Progreso guardado.")
        return []

class ActionCargarAutosaveMongo(Action):
    """Simula carga desde Mongo. Cambia por tu integración real."""
    def name(self) -> Text:
        return "action_cargar_autosave_mongo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List:
        sid = _sender_id(tracker)
        data = _INMEM_AUTOSAVE.get(sid) or {}
        events: List = []
        for k, v in data.items():
            events.append(SlotSet(k, v))
        if data:
            dispatcher.utter_message(text="📂 He cargado tu progreso guardado.")
        else:
            dispatcher.utter_message(text="ℹ️ No encontré progreso previo para reanudar.")
        return events

class ActionAutoresumeConversacion(Action):
    def name(self) -> Text:
        return "action_autoresume_conversacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List:
        if tracker.get_slot("encuesta_activa"):
            dispatcher.utter_message(text="🔄 Retomando tu proceso donde lo dejaste…")
            dispatcher.utter_message(response="utter_reanudar_conversacion")
            return [ConversationResumed()]
        dispatcher.utter_message(text="No hay nada pendiente. Continuamos normalmente.")
        return []

class ActionResetConversacionSegura(Action):
    def name(self) -> Text:
        return "action_reset_conversacion_segura"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List:
        # Limpia flags y (opcional) pausa conversación
        sid = _sender_id(tracker)
        _INMEM_AUTOSAVE.pop(sid, None)
        return [
            SlotSet("encuesta_activa", False),
            SlotSet("autosave_estado", None),
            SlotSet("encuesta_tipo", None),
            ConversationPaused(),
        ]
