from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Text

from ..core.llm_engine import run_llm
from ..core.prompts import PROMPT_SYSTEM


class ActionSoporteLLM(Action):

    def name(self) -> Text:
        return "action_soporte_llm"

    def run(self, dispatcher, tracker, domain):

        problema = tracker.latest_message.get("text", "")

        prompt = f"""
{PROMPT_SYSTEM}

Eres soporte técnico del SENA.

PROBLEMA:
{problema}

Da solución paso a paso (máx 5 pasos).
"""

        respuesta = run_llm(
           prompt,
           fallback="Revisa conexión, navegador y sesión."
        )

        dispatcher.utter_message(
            text=respuesta
        )

        return []