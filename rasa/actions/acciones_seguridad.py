# ruta: rasa/actions/acciones_seguridad.py
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ConversationPaused, EventType

from .acciones_encuesta import ActionRegistrarEncuesta


class ActionVerificarEstadoEncuesta(Action):
    def name(self) -> Text:
        return "action_verificar_estado_encuesta"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        encuesta_activa = bool(tracker.get_slot("encuesta_activa"))

        if encuesta_activa:
            # Versión segura: avisa que hay algo activo antes de cerrar
            dispatcher.utter_message(response="utter_confirmar_cierre_seguro")
            return []

        # Si no hay encuesta activa, cierre seguro directo
        dispatcher.utter_message(response="utter_cierre_confirmado_seguro")
        return [ConversationPaused()]


class ActionGuardarProgresoEncuesta(Action):
    def name(self) -> Text:
        return "action_guardar_progreso_encuesta"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        # Mensaje estándar mientras guardamos
        dispatcher.utter_message(response="utter_guardando_progreso")

        # 🔗 Conecta con ActionRegistrarEncuesta para persistencia real
        encuesta_data = {
            "usuario": tracker.sender_id,
            "estado": "pendiente",
            # Aquí probablemente querrás usar encuesta_tipo, no encuesta_activa
            "tipo": tracker.get_slot("encuesta_tipo"),
            "comentario": tracker.latest_message.get("text"),
        }
        ActionRegistrarEncuesta().registrar_en_base(encuesta_data)

        # Marcamos que ya no hay encuesta activa (quedó guardada)
        return [SlotSet("encuesta_activa", False)]


class ActionTerminarConversacionSegura(Action):
    def name(self) -> Text:
        return "action_terminar_conversacion_segura"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        """
        Esta acción asume que, si había encuesta activa, ya se llamó antes a
        ActionGuardarProgresoEncuesta (por regla o historia).
        Aquí simplemente se finaliza la conversación de forma segura.
        """
        dispatcher.utter_message(response="utter_cierre_confirmado_seguro")

        return [
            SlotSet("encuesta_activa", False),
            ConversationPaused(),
        ]


class ActionIrMenuPrincipal(Action):
    def name(self) -> Text:
        return "action_ir_menu_principal"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        # Usamos el utter_menu_principal global que ya tienes definido en otros domain_parts
        dispatcher.utter_message(response="utter_menu_principal")
        return []
