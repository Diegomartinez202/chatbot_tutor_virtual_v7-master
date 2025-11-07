# rasa/actions/acciones_encuesta.py
from __future__ import annotations
from typing import Dict, List, Any
import os, json, datetime
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionRegistrarEncuesta(Action):
    def name(self) -> str:
        return "action_registrar_encuesta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        satisfaccion = tracker.latest_message.get('intent', {}).get('name', 'desconocido')
        comentario = tracker.latest_message.get('text', 'sin comentario')
        usuario = tracker.get_slot("usuario") or "anónimo"
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        registro = {"usuario": usuario, "satisfaccion": satisfaccion, "comentario": comentario, "fecha": fecha}
        ruta = "data/encuestas.json"
        os.makedirs("data", exist_ok=True)
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")

        dispatcher.utter_message(text="✅ Registro de satisfacción guardado correctamente.")
        return []

class ActionPreguntarResolucion(Action):
    def name(self) -> str:
        return "action_preguntar_resolucion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        dispatcher.utter_message(response="utter_esta_resuelto")
        return []
