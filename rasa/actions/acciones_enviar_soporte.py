# ruta: rasa/actions/acciones_enviar_soporte.py
from __future__ import annotations
from typing import Any, Dict, List, Text
import os, json, datetime
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType

_STORE_DIR = "data"
_TICKETS_FILE = os.path.join(_STORE_DIR, "soporte.jsonl")

def _append_ticket(record: Dict[str, Any]) -> bool:
    try:
        os.makedirs(_STORE_DIR, exist_ok=True)
        with open(_TICKETS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False

class ActionEnviarSoporte(Action):
    def name(self) -> Text:
        return "action_enviar_soporte"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        # Toma lo que haya disponible (slots o último texto)
        nombre  = (tracker.get_slot("nombre") or "").strip() or "Usuario"
        email   = (tracker.get_slot("email") or "").strip() or "sin-correo@ejemplo.com"
        motivo  = (tracker.get_slot("motivo_soporte") or "").strip() or "otro"
        mensaje = (tracker.get_slot("soporte_mensaje") or tracker.latest_message.get("text") or "").strip() or "Solicitud de soporte (sin detalle)."
        prefer  = (tracker.get_slot("prefer_contacto") or "").strip() or "email"
        phone   = (tracker.get_slot("phone") or "").strip()

        payload = {
            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sender_id": tracker.sender_id,
            "nombre": nombre,
            "email": email,
            "motivo": motivo,
            "mensaje": mensaje,
            "prefer_contacto": prefer,
            "phone": phone,
            "ultimo_intent": (tracker.latest_message.get("intent") or {}).get("name"),
        }

        ok = _append_ticket(payload)

        if ok:
            dispatcher.utter_message(response="utter_soporte_creado")
        else:
            dispatcher.utter_message(response="utter_soporte_error")

        return []
