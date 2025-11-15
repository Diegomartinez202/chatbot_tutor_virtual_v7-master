# ruta: rasa/actions/acciones_encuesta.py
from __future__ import annotations
from typing import Dict, List, Any, Text
import os, json, datetime
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType
from rasa_sdk.forms import FormValidationAction

_DATA_DIR = "data"
_ENC_FILE = os.path.join(_DATA_DIR, "encuestas.jsonl")

def _ensure_store() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.exists(_ENC_FILE):
        with open(_ENC_FILE, "w", encoding="utf-8") as f:
            f.write("")

def _append_jsonl(record: Dict[str, Any]) -> None:
    _ensure_store()
    with open(_ENC_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

class ActionRegistrarEncuesta(Action):
    def name(self) -> str:
        return "action_registrar_encuesta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]) -> List[EventType]:
        satisfaccion = tracker.get_slot("nivel_satisfaccion") or tracker.latest_message.get('intent', {}).get('name', 'desconocido')
        comentario   = tracker.get_slot("comentario") or tracker.latest_message.get('text', 'sin comentario')
        usuario      = tracker.get_slot("usuario") or tracker.sender_id or "anónimo"
        fecha        = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        registro = {"usuario": usuario, "satisfaccion": satisfaccion, "comentario": comentario, "fecha": fecha}
        _append_jsonl(registro)

        dispatcher.utter_message(text="✅ Registro de satisfacción guardado correctamente.")
        return [
            SlotSet("encuesta_incompleta", False),
            SlotSet("proceso_activo", None),]

class ActionGuardarFeedback(Action):
    def name(self) -> str:
        return "action_guardar_feedback"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]) -> List[EventType]:
        feedback = tracker.get_slot("feedback_texto") or tracker.latest_message.get("text", "").strip()
        usuario  = tracker.get_slot("usuario") or tracker.sender_id or "anónimo"
        fecha    = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if feedback:
            _append_jsonl({"usuario": usuario, "feedback": feedback, "fecha": fecha, "tipo": "comentario"})
            dispatcher.utter_message(response="utter_gracias_retroalimentacion")
        else:
            dispatcher.utter_message(text="📝 No recibí un comentario. ¿Quieres intentar de nuevo?")
        return []

class ActionPreguntarResolucion(Action):
    def name(self) -> str:
        return "action_preguntar_resolucion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        dispatcher.utter_message(response="utter_esta_resuelto")
        return [
            SlotSet("encuesta_incompleta", True),
            SlotSet("proceso_activo", "encuesta_satisfaccion"),
        ]

class ActionSetEncuestaTipo(Action):
    def name(self) -> Text: 
        return "action_set_encuesta_tipo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]) -> List[EventType]:
        intent = (tracker.latest_message.get("intent") or {}).get("name", "")
        # Mapear intent → tipo
        tipo = "positivo" if intent in ("encuesta_satis_yes", "respuesta_satisfecho") else \
               "negativo" if intent in ("encuesta_satis_no", "respuesta_insatisfecho") else "neutro"
        return [SlotSet("encuesta_tipo", tipo)]

class ValidateEncuestaSatisfaccionForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_encuesta_satisfaccion_form"

    def validate_nivel_satisfaccion(self, value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]) -> Dict[Text, Any]:
        v = (value or "").strip().lower()
        validos = {"excelente", "buena", "regular", "mala", "satisfecho", "neutral", "insatisfecho"}
        if v in validos:
            return {"nivel_satisfaccion": v}
        dispatcher.utter_message(text="💡 Usa una opción válida: excelente, buena, regular o mala.")
        return {"nivel_satisfaccion": None}

    def validate_comentario(self, value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]) -> Dict[Text, Any]:
        v = (value or "").strip()
        if not v:
            dispatcher.utter_message(text="📝 Déjanos un breve comentario (puede ser una frase corta).")
            return {"comentario": None}
        if len(v) > 1000:
            dispatcher.utter_message(text="✂️ El comentario es muy largo. Resume en menos de 1000 caracteres.")
            return {"comentario": None}
        return {"comentario": v}

class ActionVerificarEstadoEncuesta(Action):
    def name(self) -> Text:
        return "action_verificar_estado_encuesta"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        """Verifica si hay una encuesta activa o pendiente y actualiza el slot `encuesta_activa`."""

        # Slots relevantes
        encuesta_activa_slot = tracker.get_slot("encuesta_activa")
        encuesta_incompleta = tracker.get_slot("encuesta_incompleta")
        autosave_estado = tracker.get_slot("autosave_estado")

        nivel_satisfaccion = tracker.get_slot("nivel_satisfaccion")
        encuesta_tipo = tracker.get_slot("encuesta_tipo")
        comentario = tracker.get_slot("comentario")

        # 1) ¿Hay algo guardado en autosave que parezca relacionado con una encuesta?
        autosave_tiene_encuesta = False
        if isinstance(autosave_estado, str) and autosave_estado.strip():
            autosave_tiene_encuesta = "encuesta" in autosave_estado.lower()

        # 2) ¿Hay datos parciales de la encuesta de satisfacción?
        encuesta_slots = [nivel_satisfaccion, encuesta_tipo, comentario]
        algun_dato_encuesta = any(
            s is not None and str(s).strip() != "" for s in encuesta_slots
        )
        encuesta_completa = all(
            s is not None and str(s).strip() != "" for s in encuesta_slots
        )
        encuesta_pendiente = algun_dato_encuesta and not encuesta_completa

        # 3) Consolidar criterio de "encuesta activa"
        hay_encuesta_activa = bool(encuesta_activa_slot) or bool(encuesta_incompleta) \
            or autosave_tiene_encuesta or encuesta_pendiente

        logger.info(
            "[action_verificar_estado_encuesta] encuesta_activa_slot=%r, "
            "encuesta_incompleta=%r, autosave_estado_present=%r, "
            "autosave_tiene_encuesta=%r, algun_dato_encuesta=%r, "
            "encuesta_completa=%r, encuesta_pendiente=%r -> hay_encuesta_activa=%r",
            encuesta_activa_slot,
            encuesta_incompleta,
            bool(autosave_estado),
            autosave_tiene_encuesta,
            algun_dato_encuesta,
            encuesta_completa,
            encuesta_pendiente,
            hay_encuesta_activa,
        )

        # Mensaje opcional al usuario según el estado
        if hay_encuesta_activa:
            dispatcher.utter_message(
                text="Veo que tienes una encuesta o proceso pendiente. Podemos retomarlo antes de cerrar."
            )
        else:
            dispatcher.utter_message(
                text="No tienes encuestas activas. Podemos cerrar la conversación de forma segura."
            )

        # Actualizamos el slot para que las rules lo usen
        eventos: List[EventType] = [SlotSet("encuesta_activa", hay_encuesta_activa)]

        # Opcional: también puedes actualizar encuesta_incompleta según el cálculo
        eventos.append(SlotSet("encuesta_incompleta", encuesta_pendiente))

        return eventos