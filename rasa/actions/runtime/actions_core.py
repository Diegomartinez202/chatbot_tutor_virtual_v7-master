from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
from typing import List, Dict, Text, Any

from ..core.llm_engine import run_llm
from ..core.prompts import PROMPT_SYSTEM
from ..core.nlp_utils import detectar_materia


# =====================================================
# 1. EXPLICAR TEMA (ESTABLE)
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

        prompt = f"""
{PROMPT_SYSTEM}

Explica el siguiente tema de forma pedagógica:

TEMA: {tema}
"""

        respuesta = run_llm(
            prompt,
            fallback=f"No pude explicar {tema}"
)

        dispatcher.utter_message(
            text=respuesta
        )

        return [
            SlotSet("tema_actual", tema),
            SlotSet("from_llm", True),
        ]