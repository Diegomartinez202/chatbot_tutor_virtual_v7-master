from __future__ import annotations
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType

MAX_INTENTOS_FORM = 3  # puedes moverlo a ENV si lo deseas

class ActionRegistrarIntentoForm(Action):
    """Incrementa el slot soporte_intentos en 1 durante el form."""

    def name(self) -> Text:
        return "action_registrar_intento_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        intentos = tracker.get_slot("soporte_intentos") or 0
        intentos = int(intentos) + 1
        return [SlotSet("soporte_intentos", intentos)]


class ActionVerificarMaxIntentosForm(Action):
    """Si supera el máximo, una rule puede cortar el form y derivar a humano."""

    def name(self) -> Text:
        return "action_verificar_max_intentos_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        intentos = int(tracker.get_slot("soporte_intentos") or 0)
        if intentos >= MAX_INTENTOS_FORM:
            dispatcher.utter_message(response="utter_handoff_por_fallos")
            # Reiniciamos el contador para futuros formularios
            return [SlotSet("soporte_intentos", 0)]
        else:
            dispatcher.utter_message(response="utter_intento_form_fallido")
        return []


class ActionOfrecerHumano(Action):
    def name(self) -> Text:
        return "action_ofrecer_humano"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        dispatcher.utter_message(response="utter_ofrecer_humano")
        return []


class ActionHandoffCancelar(Action):
    def name(self) -> Text:
        return "action_handoff_cancelar"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        dispatcher.utter_message(response="utter_derivacion_cancelada")
        return [SlotSet("derivacion_humano", False)]


class ActionDerivarHumanoConfirmada(Action):
    """Se ejecuta tras la confirmación explícita del usuario para derivar a humano."""

    def name(self) -> Text:
        return "action_derivar_humano_confirmada"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        dispatcher.utter_message(response="utter_derivar_humano_en_progreso")
        # Aquí podrías llamar a otra acción/ticket si quieres (o a un backend)
        return []


class ActionCancelarDerivacion(Action):
    """Responde cuando el usuario niega la derivación a humano."""

    def name(self) -> Text:
        return "action_cancelar_derivacion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        dispatcher.utter_message(response="utter_derivacion_cancelada")
        return [SlotSet("derivacion_humano", False)]

class ActionDerivarYRegistrarHumano(Action):
    def name(self) -> Text:
        return "action_derivar_y_registrar_humano"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: dict
    ) -> List[EventType]:
        """
        Marca la derivación a humano y notifica al usuario.

        - Muestra el mensaje de derivación en curso.
        - Muestra el mensaje de 'en cola con un asesor humano' (utter_handoff_en_cola).
        - Actualiza los slots relacionados con la derivación.
        """

        # Mensaje actual que ya usabas
        dispatcher.utter_message(response="utter_derivando_humano")

        # 👉 Nuevo mensaje: en cola con humano
        dispatcher.utter_message(response="utter_handoff_en_cola")

        # Slots (mantengo tu lógica tal cual)
        return [
            SlotSet("derivacion_humano", True),
            SlotSet("proceso_activo", "soporte_humano"),
            SlotSet("derivacion_humano", False),
            SlotSet("proceso_activo", None),
        ]

class ActionHandoffEnCola(Action):
    def name(self) -> Text:
        return "action_handoff_en_cola"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        """
        Informa al usuario que fue puesto en cola con un asesor humano
        y muestra botones para:
          - terminar la conversación guardando progreso,
          - o volver al menú principal.
        """
        dispatcher.utter_message(response="utter_handoff_en_cola")
        return []