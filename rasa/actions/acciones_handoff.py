from __future__ import annotations
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType, FollowupAction

MAX_INTENTOS_FORM = 3  # puedes moverlo a ENV si lo deseas


# ======================================================
# 🧪 CONTROL DE INTENTOS DE FORM / DERIVACIÓN
# ======================================================
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


# ======================================================
# 🤝 OFRECER HUMANO / MANEJO DE HANDOFF
# ======================================================
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

        # Mensaje de transición
        dispatcher.utter_message(response="utter_derivar_humano_en_progreso")

        # 👉 Le decimos a Rasa: ahora ejecuta la acción master de handoff.
        return [FollowupAction("action_derivar_y_registrar_humano")]


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


# ======================================================
# 🧑‍💼 DERIVAR Y REGISTRAR HUMANO + RESUMEN LLM
# ======================================================

def _build_handoff_base_text(tracker: Tracker) -> str:
    """
    Construye un texto base 'técnico' para que el LLM genere
    un resumen del caso para el agente humano.

    ⚠️ Importante:
    - No ponemos correos, teléfonos ni documentos como texto literal.
    - Nos centramos en el problema y contexto general.
    """
    motivo = (tracker.get_slot("motivo_soporte") or "soporte general").strip()
    tipo_soporte = (tracker.get_slot("tipo_soporte") or "interno").strip()
    ultimo_intent = (tracker.latest_message.get("intent") or {}).get("name")
    ultimo_mensaje = (tracker.latest_message.get("text") or "").strip()

    texto_base = (
        "Genera un resumen breve y claro del caso para un agente humano de soporte.\n"
        f"- Tipo de soporte: {tipo_soporte}\n"
        f"- Motivo principal reportado: {motivo}\n"
        f"- Último intent detectado por el bot: {ultimo_intent}\n"
        f"- Último mensaje del usuario (no incluyas datos de contacto literal): \"{ultimo_mensaje}\"\n\n"
        "El resumen debe centrarse en el problema descrito, el contexto que el usuario ha dado "
        "y el estado actual (por ejemplo: 'formulario de soporte en curso', 'varios intentos fallidos', etc.). "
        "No incluyas correos, teléfonos, números de documento ni URLs exactas, solo describe el caso."
    )
    return texto_base


class ActionDerivarYRegistrarHumano(Action):
    def name(self) -> Text:
        return "action_derivar_y_registrar_humano"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: dict,
    ) -> List[EventType]:
        """
        Marca la derivación a humano y notifica al usuario.

        - Muestra el mensaje de derivación en curso.
        - Muestra el mensaje de 'en cola con un asesor humano' (utter_handoff_en_cola).
        - Actualiza los slots relacionados con la derivación.
        - (Nuevo) Genera un resumen del caso para el agente humano usando el LLM
          y lo deja en logs (o se puede enviar a Guardian/Helpdesk en el futuro).
        """

        # Mensaje actual que ya usabas
        dispatcher.utter_message(response="utter_derivando_humano")

        # 👉 Nuevo mensaje: en cola con humano
        dispatcher.utter_message(response="utter_handoff_en_cola")

        # ✨ NUEVO: Resumen del caso para el agente humano (no se muestra al usuario)
        try:
            texto_base = _build_handoff_base_text(tracker)
            contexto_llm = {
                "flujo": "guardian_handoff",
                "motivo_soporte": tracker.get_slot("motivo_soporte") or "soporte general",
            }
            resumen = llm_summarize_with_ollama(texto_base, contexto_llm)
            # Por ahora lo dejamos en logs; en tu proyecto de grado puedes mostrar
            # que este resumen se podría enviar a tu sistema de Helpdesk.
            logger.info("[HANDOFF_RESUMEN_LLM] sender_id=%s resumen=%s", tracker.sender_id, resumen)
        except Exception:
            logger.exception("Error generando resumen LLM para handoff a humano")

        # Slots (mantengo tu lógica tal cual estaba)
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