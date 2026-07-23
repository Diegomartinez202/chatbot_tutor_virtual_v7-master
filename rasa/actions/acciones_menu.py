# ruta: rasa/actions/acciones_menu.py

from __future__ import annotations

from typing import Any, Dict, List, Text
import logging

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, EventType

logger = logging.getLogger(__name__)


class ActionIrMenuPrincipal(Action):

    def name(self) -> Text:
        return "action_ir_menu_principal"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info(
            "[MENU] user=%s -> principal",
            tracker.sender_id,
        )

        dispatcher.utter_message(
            response="utter_menu_principal"
        )

        return [

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "menu_actual",
                "principal"
            )
        ]


class ActionIrMenuAcademico(Action):

    def name(self) -> Text:
        return "action_ir_menu_academico"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info(
            "[MENU] user=%s -> academico",
            tracker.sender_id,
        )

        dispatcher.utter_message(
            response="utter_menu_academico"
        )

        return [
            SlotSet(
                "menu_actual",
                "academico"
            )
        ]


class ActionIrMenuSoporte(Action):

    def name(self) -> Text:
        return "action_ir_menu_soporte"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info(
            "[MENU] user=%s -> soporte",
            tracker.sender_id,
        )

        dispatcher.utter_message(
            response="utter_menu_soporte"
        )

        return [
            SlotSet(
                "menu_actual",
                "soporte"
            )
        ]


class ActionIrMenuAdministrativo(Action):

    def name(self) -> Text:
        return "action_ir_menu_administrativo"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info(
            "[MENU] user=%s -> administrativo",
            tracker.sender_id,
        )

        dispatcher.utter_message(
            response="utter_menu_administrativo"
        )

        return [
            SlotSet(
                "menu_actual",
                "administrativo"
            )
        ]