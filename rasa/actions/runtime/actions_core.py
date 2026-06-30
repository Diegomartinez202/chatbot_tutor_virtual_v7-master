from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
from typing import List, Dict, Text, Any

# Importamos la función de historial reducido
from ..core.llm_engine import run_llm, get_last_turns 
from ..core.prompts import PROMPT_SYSTEM
from ..core.nlp_utils import detectar_materia


# =====================================================
# 1. EXPLICAR TEMA (OPTIMIZADO)
# =====================================================
class ActionExplicarTemaLLM(Action):

    def name(self) -> Text:
        return "action_explicar_tema_llm"

    def run(self, dispatcher, tracker, domain):

        tema = (
            tracker.get_slot("tema_actual")
            or tracker.get_slot("tema_academico")
            or "tema académico"
        )

        # Obtenemos solo los últimos 2 mensajes para dar contexto sin saturar la CPU
        historial_breve = get_last_turns(tracker, n=2)

        # Construimos el prompt integrando el historial reducido
        prompt = f"""
{PROMPT_SYSTEM}

CONTEXTO RECIENTE:
{historial_breve}

Explica el siguiente tema de forma pedagógica:
TEMA: {tema}
"""

        # La llamada ahora es más eficiente gracias al prompt reducido
        respuesta = run_llm(
            prompt,
            tracker=tracker, # Pasamos el tracker para que el motor pueda validarlo
            fallback=f"No pude explicar {tema}"
        )

        dispatcher.utter_message(
            text=respuesta
        )

        return [
            SlotSet("tema_actual", tema),
            SlotSet("from_llm", True),
        ]