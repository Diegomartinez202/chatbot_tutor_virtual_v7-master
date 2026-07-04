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
    def name(self):
        return "action_explicar_tema_llm"

    def run(self, dispatcher, tracker, domain):
        # Capturamos el tema (si es una respuesta nueva o una continuación)
        user_text = tracker.latest_message.get("text", "")
        
        eventos = [
            SlotSet("proceso_activo", "aprender_tema")
        ]
        
        # Si no estamos continuando, actualizamos el slot de tema
        if tracker.get_intent_of_latest_message() != "continuar_tema":
            eventos.append(SlotSet("tema_actual", user_text))
            
        return eventos + [FollowupAction("action_handle_with_llm")]