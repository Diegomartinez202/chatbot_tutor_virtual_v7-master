# ruta: rasa/actions/acciones_soporte.py
from __future__ import annotations

import logging
import time
import os
import json
import datetime
from typing import Any, Dict, List, Text, Optional

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    EventType,
    FollowupAction,
)
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict
from .core.llm_engine import run_llm, get_last_turns
from .utils_logging import get_logger

logger = get_logger(__name__)

from .common import (
    jlog,
    EMAIL_RE,
    HELPDESK_WEBHOOK,
    HELPDESK_TOKEN,
    _entity_value,
    _json_payload_from_text,
    post_json_with_retries,
)

_STORE_DIR = "data"
_TICKETS_FILE = os.path.join(_STORE_DIR, "soporte.jsonl")
MAX_INTENTOS_FORM = 2  


def _append_ticket_local(record: Dict[str, Any]) -> bool:
    """Guarda un registro de soporte en data/soporte.jsonl (log local)."""
    try:
        os.makedirs(_STORE_DIR, exist_ok=True)
        with open(_TICKETS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception:
        logger.exception("[SOPORTE_LOCAL] Error al escribir ticket local")
        return False


class ValidateSoporteForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_soporte_form"

    def validate_nombre(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        v = (value or "").strip()
        if len(v) < 3:
            dispatcher.utter_message(
                text="⚠️ El nombre debe tener al menos 3 caracteres."
            )
            return {"nombre": None}
        if len(v) > 120:
            dispatcher.utter_message(
                text="⚠️ El nombre es muy largo. ¿Puedes abreviarlo un poco?"
            )
            return {"nombre": None}
        return {"nombre": v}

    def validate_email(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        v = (value or "").strip()
        if not EMAIL_RE.match(v):
            dispatcher.utter_message(
                text="📧 Ese email no parece válido. Escribe algo como usuario@dominio.com"
            )
            return {"email": None}
        return {"email": v}

    def validate_mensaje(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        v = (value or "").strip()
        if len(v) < 8:
            dispatcher.utter_message(
                text="📝 Dame un poco más de detalle del problema (mínimo 8 caracteres)."
            )
            return {"mensaje": None}
        if len(v) > 5000:
            dispatcher.utter_message(
                text="📝 El mensaje es muy largo. Intenta resumirlo (máx. 5000)."
            )
            return {"mensaje": None}
        return {"mensaje": v}


class ActionEnviarSoporte(Action):
    def name(self) -> Text:
        return "action_enviar_soporte"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        nombre_ent = _entity_value(tracker, "nombre")
        email_ent = _entity_value(tracker, "email")
        mensaje_ent = _entity_value(tracker, "mensaje")
        latest = tracker.latest_message or {}
        last_text = (tracker.latest_message.get("text") or "").strip()
        json_payload = _json_payload_from_text(last_text)

        nombre = (
            nombre_ent
            or json_payload.get("nombre")
            or (tracker.get_slot("nombre") or "Usuario")
        ).strip()
        
        email = (
            email_ent
            or json_payload.get("email")
            or (tracker.get_slot("email") or "sin-correo@zajuna.edu")
        ).strip()

        mensaje = (
            mensaje_ent
            or json_payload.get("mensaje")
            or (tracker.get_slot("mensaje") or "")
        ).strip()
        
        if not mensaje:
            mensaje = (
                last_text
                if not last_text.startswith("/enviar_soporte")
                else "Solicitud de soporte (sin detalle)."
            )

        if len(nombre) > 120:
            nombre = nombre[:120].rstrip() + "…"
        if len(mensaje) > 5000:
            mensaje = mensaje[:5000].rstrip() + "…"

        if not EMAIL_RE.match(email):
            logger.warning(
                "[actions] Email inválido en action_enviar_soporte: %r, usando fallback.",
                email,
            )
            email = "sin-correo@zajuna.edu"

        meta = {
            "rasa_sender_id": tracker.sender_id,
            "latest_intent": (latest.get("intent") or {}).get("name"),
            "timestamp": int(time.time()),
            "slots": tracker.current_slot_values(),
            "metadata": latest.get("metadata") or {},
        }
        
        payload = {
            "name": nombre,
            "email": email,
            "subject": "Soporte rápido (Rasa)",
            "message": mensaje or "Solicitud de soporte (sin detalle).",
            "conversation_id": tracker.sender_id,
            "metadata": meta,
        }

        _append_ticket_local(
            {
                "fecha": datetime.datetime.utcnow().isoformat(),
                "sender_id": tracker.sender_id,
                "name": nombre,
                "email": email,
                "subject": payload["subject"],
                "message": payload["message"],
                "meta": meta,
            }
        )

        headers = {"Content-Type": "application/json"}
        if HELPDESK_TOKEN:
            headers["Authorization"] = f"Bearer {HELPDESK_TOKEN}"

        resp = post_json_with_retries(HELPDESK_WEBHOOK, payload, headers)
        ok = bool(resp and 200 <= getattr(resp, "status_code", 0) < 300)
        
        jlog(
            logging.INFO,
            "action_enviar_soporte",
            ok=ok,
            status_code=getattr(resp, "status_code", None),
        )

        if ok:
            texto_base = (
                "Se ha registrado una solicitud de soporte rápido para el usuario. "
                "El sistema enviará el ticket al equipo de ayuda y un agente lo revisará. "
                "Genera un mensaje breve y empático agradeciendo al usuario por la información, "
                "indicando que un agente lo contactará por el medio registrado y que, si el problema es urgente, "
                "puede revisar también los canales oficiales de soporte."
            )
            contexto_llm = {
                "flujo": "soporte_rapido",
                "tiene_correo_valido": bool(email),
            }
            historial_reducido = get_last_turns(tracker, n=2)
            prompt_soporte = f"{historial_reducido}\n\nInstrucción: {texto_base}"

            try:
                # MEJORA: Corrección del texto del parámetro fallback para alinearlo al dominio de soporte
                mensaje_llm = run_llm(
                    prompt=prompt_soporte,
                    tracker=tracker,
                    context=contexto_llm,
                    fallback="✅ He enviado tu solicitud de soporte de forma exitosa. Un agente de soporte la revisará."
                )
                if mensaje_llm and mensaje_llm.strip():
                    dispatcher.utter_message(text=mensaje_llm.strip())
                else:
                    dispatcher.utter_message(
                        text="✅ He enviado tu solicitud de soporte. Un agente te contactará."
                    )
            except Exception:
                dispatcher.utter_message(
                    text="✅ He enviado tu solicitud de soporte. Un agente te contactará."
                )
        else:
            dispatcher.utter_message(
                text=(
                    "⚠️ No pude registrar el soporte ahora mismo. "
                    "Por favor, inténtalo de nuevo más tarde o pide hablar con un asesor humano."
                )
            )

        return []


class ActionSoporteSubmit(Action):
    def name(self) -> Text:
        return "action_soporte_submit"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        latest = tracker.latest_message or {}

        tipo_soporte = (tracker.get_slot("tipo_soporte") or "interno").strip()
        motivo = (tracker.get_slot("motivo_soporte") or "").strip()
        prefer_contacto = (tracker.get_slot("prefer_contacto") or "").strip()
        telefono = (tracker.get_slot("telefono") or "").strip()
        soporte_mensaje = (tracker.get_slot("soporte_mensaje") or "").strip()

        nombre = (tracker.get_slot("nombre") or "").strip()
        email = (tracker.get_slot("email") or "").strip()
        mensaje_slot = (tracker.get_slot("mensaje") or "").strip()

        mensaje = mensaje_slot or soporte_mensaje

        if not (nombre and email and mensaje):
            dispatcher.utter_message(
                text="❌ Faltan datos para crear el ticket de soporte."
            )
            return []

        meta = {
            "rasa_sender_id": tracker.sender_id,
            "latest_intent": (latest.get("intent") or {}).get("name"),
            "timestamp": int(time.time()),
            "slots": tracker.current_slot_values(),
            "metadata": latest.get("metadata") or {},
        }

        subject = (
            "PQRS - Soporte técnico (Rasa)"
            if tipo_soporte == "pqrs"
            else "Soporte técnico (Rasa)"
        )

        payload = {
            "name": nombre,
            "email": email,
            "subject": subject,
            "message": mensaje,
            "conversation_id": tracker.sender_id,
            "tipo_soporte": tipo_soporte,
            "motivo_soporte": motivo,
            "prefer_contacto": prefer_contacto,
            "telefono": telefono,
            "metadata": meta,
        }

        headers = {"Content-Type": "application/json"}
        if HELPDESK_TOKEN:
            headers["Authorization"] = f"Bearer {HELPDESK_TOKEN}"

        resp = post_json_with_retries(
            HELPDESK_WEBHOOK,
            payload,
            headers,
        )

        ok = bool(
            resp and 200 <= getattr(resp, "status_code", 0) < 300
        )

        jlog(
            logging.INFO,
            "action_soporte_submit",
            ok=ok,
            status_code=getattr(resp, "status_code", None),
        )

        events: List[EventType] = [
            SlotSet("nombre", None),
            SlotSet("email", None),
            SlotSet("mensaje", None),
            SlotSet("soporte_mensaje", None),
            SlotSet("tipo_soporte", None),
        ]

        if ok:
            resumen_motivo = motivo or "soporte general"
            resumen_mensaje = (mensaje or "").strip()

            if len(resumen_mensaje) > 400:
                resumen_mensaje = (
                    resumen_mensaje[:400].rstrip() + "…"
                )

            if tipo_soporte == "pqrs":
                texto_base = (
                    "He registrado tu caso como PQRS formal para el equipo de soporte. "
                    "Un asesor revisará tu solicitud y te contactará con la información registrada.\n\n"
                    f"Motivo principal: {resumen_motivo}\n"
                    f"Descripción del problema: {resumen_mensaje}"
                )
            else:
                texto_base = (
                    "He registrado tu solicitud de soporte interno para la plataforma. "
                    "Un asesor la revisará y se comunicará contigo según tu preferencia de contacto.\n\n"
                    f"Motivo principal: {resumen_motivo}\n"
                    f"Descripción del problema: {resumen_mensaje}"
                )

            contexto_llm = {
                "flujo": "soporte_tecnico",
                "tipo_soporte": tipo_soporte,
                "motivo_soporte": resumen_motivo,
                "prefer_contacto": (prefer_contacto or "no_especificado"),
            }

            mensaje_final = run_llm(
                prompt=texto_base,
                tracker=tracker,
                context=contexto_llm,
                fallback=(
                    "✅ Tu solicitud fue registrada correctamente. "
                    "Un asesor revisará el caso y se comunicará contigo."
                ),
            )

            dispatcher.utter_message(text=mensaje_final)

            if tracker.get_slot("escalar_humano"):
                events.append(
                    FollowupAction("action_derivar_y_registrar_humano")
                )
            else:
                dispatcher.utter_message(
                    response="utter_preguntar_satisfaccion"
                )

            events.append(SlotSet("escalar_humano", False))
            return events

        dispatcher.utter_message(
            text=(
                "⚠️ Ocurrió un problema al registrar tu soporte. "
                "Por favor, inténtalo de nuevo más tarde o pide hablar con un asesor humano."
            )
        )
        return events


class ActionEnviarCorreoTutor(Action):
    def name(self) -> Text:
        return "action_enviar_correo_tutor"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        email = (tracker.get_slot("email") or "").strip()
        if not email or not EMAIL_RE.match(email):
            dispatcher.utter_message(
                text="Necesito un correo válido para escribirle al tutor. Por favor, indícalo."
            )
            return []

        payload = {
            "to": "tutor@zajuna.edu",
            "from": email,
            "subject": "Contacto con tutor (Rasa)",
            "message": f"El estudiante con correo {email} solicita apoyo adicional.",
        }
        headers = {"Content-Type": "application/json"}
        if HELPDESK_TOKEN:
            headers["Authorization"] = f"Bearer {HELPDESK_TOKEN}"

        resp = post_json_with_retries(HELPDESK_WEBHOOK, payload, headers)
        ok = bool(resp and 200 <= getattr(resp, "status_code", 0) < 300)
        
        jlog(
            logging.INFO,
            "action_enviar_correo_tutor",
            ok=ok,
            status_code=getattr(resp, "status_code", None),
        )

        dispatcher.utter_message(
            response="utter_correo_enviado" if ok else "utter_soporte_error"
        )
        return []


class ActionMarcarEscalarHumano(Action):
    def name(self) -> Text:
        return "action_marcar_escalar_humano"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        return [SlotSet("escalar_humano", True)]


class ActionRegistrarIntentoForm(Action):
    def name(self) -> Text:
        return "action_registrar_intento_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        """Incrementa el contador SOLO si el slot pedido es mensaje/soporte_mensaje."""
        requested_slot = tracker.get_slot("requested_slot")

        if requested_slot not in ("mensaje", "soporte_mensaje"):
            return []

        actual = tracker.get_slot("soporte_form_fallback_count") or 0
        nuevo = float(actual) + 1.0

        return [SlotSet("soporte_form_fallback_count", nuevo)]


class ActionVerificarMaxIntentosForm(Action):
    def name(self) -> Text:
        return "action_verificar_max_intentos_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        """Solo avisa / resetea cuando el slot pedido es mensaje/soporte_mensaje."""
        requested_slot = tracker.get_slot("requested_slot")

        if requested_slot not in ("mensaje", "soporte_mensaje"):
            return []

        # MEJORA: Casting defensivo a float para evitar fallos de comparación de tipos (TypeError)
        try:
            conteo = float(tracker.get_slot("soporte_form_fallback_count") or 0)
        except (ValueError, TypeError):
            conteo = 0.0

        if conteo < float(MAX_INTENTOS_FORM):
            return []

        dispatcher.utter_message(response="utter_form_fallback_warn")
        dispatcher.utter_message(response="utter_ofrecer_humano")
        
        return [
            SlotSet("soporte_form_fallback_count", 0), 
            SlotSet("escalar_humano", True)
        ]


class ActionPQRSLLM(Action):
    """Genera y/o refina una PQRS usando el LLM central."""

    def name(self) -> Text:
        return "action_pqrs_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        logger.info("ActionPQRSLLM ejecutada.")

        dispatcher.utter_message(
            text=(
                "📝 Perfecto, voy a ayudarte a redactar tu PQRS (petición, queja, "
                "reclamo o sugerencia) de forma clara y respetuosa.\n\n"
                "Por favor cuéntame, con tus palabras, qué quieres reportar, "
                "y luego ajustaré el mensaje con lenguaje formal para que puedas "
                "enviarlo por los canales oficiales. ✅"
            )
        )

        return [FollowupAction("action_handle_with_llm")]


class ActionPreguntasFrecuentesLLM(Action):
    """Responde preguntas frecuentes (FAQ) usando el LLM central."""

    def name(self) -> Text:
        return "action_preguntas_frecuentes_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        logger.info("ActionPreguntasFrecuentesLLM ejecutada.")

        dispatcher.utter_message(
            text=(
                "❓ Veo que tienes una duda frecuente sobre la plataforma o el proceso.\n\n"
                "Voy a darte una explicación clara y resumida basada en la información "
                "académica y de soporte de Zajuna. Si después quieres más detalle, "
                "podemos profundizar o escalar a soporte humano. 🙂"
            )
        )

        return [FollowupAction("action_handle_with_llm")]


class ActionSoporteTecnicoLLM(Action):
    def name(self) -> Text:
        return "action_soporte_tecnico_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionSoporteTecnicoLLM ejecutada.")

        prompt = (
            "Genera un mensaje corto, empático y profesional para un estudiante "
            "que acaba de pedir soporte técnico en la plataforma Zajuna."
        )

        intro = run_llm(prompt, tracker=tracker)
        dispatcher.utter_message(text=intro)

        dispatcher.utter_message(
            text=(
                "🛠️ Revisemos tu problema técnico.\n\n"
                "Te ayudaré paso a paso y, si es necesario, podremos "
                "escalar el caso a soporte humano."
            )
        )

        dispatcher.utter_message(response="utter_menu_soporte")

        return [FollowupAction("action_handle_with_llm")]