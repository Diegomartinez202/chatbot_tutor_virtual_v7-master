from typing import Dict, Text, Any, List
from rasa_sdk import Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet
import json
import os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "../../data/encuestas.json")

# ----------------------------
# Validación del formulario
# ----------------------------

class ValidateEncuestaForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_encuesta_satisfaccion_form"

    async def validate_nivel_satisfaccion(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        valor = slot_value.lower()
        opciones = ["satisfecho", "neutral", "insatisfecho"]
        if valor not in opciones:
            dispatcher.utter_message(
                text=f"⚠️ Por favor selecciona una opción válida: {', '.join(opciones)}."
            )
            return {"nivel_satisfaccion": None}
        return {"nivel_satisfaccion": valor}


# ----------------------------
# Acción personalizada
# ----------------------------

from rasa_sdk import Action

class ActionGuardarEncuesta(Action):
    def name(self) -> Text:
        return "action_guardar_encuesta"

    def _cargar_encuestas(self):
        if not os.path.exists(DATA_FILE):
            return []
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def _guardar_encuestas(self, encuestas):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(encuestas, f, indent=2, ensure_ascii=False)

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict):
        usuario = tracker.sender_id
        nivel = tracker.get_slot("nivel_satisfaccion")
        comentario = tracker.get_slot("comentario")

        registro = {
            "usuario": usuario,
            "nivel_satisfaccion": nivel or "sin_dato",
            "comentario": comentario or "",
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        encuestas = self._cargar_encuestas()
        encuestas.append(registro)
        self._guardar_encuestas(encuestas)

        dispatcher.utter_message(
            text="✅ Gracias. Tu opinión ha sido registrada correctamente. ¡Nos ayuda a mejorar!"
        )

        # opcional: limpiar los slots después
        return [SlotSet("nivel_satisfaccion", None), SlotSet("comentario", None)]
