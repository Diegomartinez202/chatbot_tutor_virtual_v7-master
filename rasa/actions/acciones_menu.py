# rasa\actions\acciones_menu.py
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from .common import _has_auth

class ActionSetMenuPrincipal(Action):
    def name(self) -> Text:
        return "action_set_menu_principal"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        return [SlotSet("menu_actual", "principal")]