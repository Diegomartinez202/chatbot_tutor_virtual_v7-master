# ruta: rasa/actions/acciones_tracking.py
from __future__ import annotations

import logging
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict  # MEJORA: Importación oficial de DomainDict
from rasa_sdk.events import (
    SlotSet,
    EventType,
)
from .utils_logging import get_logger

logger = get_logger(__name__)

SESION_LARGA_UMBRAL = 8


class ActionIncrementarTurnosConversacion(Action):

    def name(self) -> Text:
        return "action_incrementar_turnos_conversacion"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        """
        Incrementa el contador de turnos y
        marca una sesión larga cuando supera
        el umbral configurado.
        """

        turnos_actual = (
            tracker.get_slot("turnos_conversacion")
            or 0.0
        )

        try:
            turnos_actual = float(turnos_actual)
        except (TypeError, ValueError):
            turnos_actual = 0.0

        nuevo_valor = turnos_actual + 1.0

        sesion_larga_slot = tracker.get_slot("sesion_larga")

        if isinstance(
            sesion_larga_slot,
            bool,
        ):
            sesion_larga = sesion_larga_slot
        else:
            sesion_larga = False

        if nuevo_valor >= SESION_LARGA_UMBRAL:
            sesion_larga = True

        logger.debug(
            "[TRACKING] turnos=%s sesion_larga=%s",
            nuevo_valor,
            sesion_larga,
        )

        return [
            SlotSet(
                "turnos_conversacion",
                nuevo_valor,
            ),
            SlotSet(
                "sesion_larga",
                sesion_larga,
            ),
        ]