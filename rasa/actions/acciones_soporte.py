# ruta: rasa/actions/acciones_soporte.py
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Text, Optional
import os
import json
import datetime

from rasa_sdk import Tracker, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType, FollowupAction
from rasa_sdk.types import DomainDict
from rasa_sdk.forms import FormValidationAction

from .acciones_llm import llm_summarize_with_ollama
from .common import (
    logger,
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


def _append_ticket_local(record: Dict[str, Any]) -> bool:
    """Guarda un registro de soporte en data/soporte.jsonl (log local)."""
    try:
        os.makedirs(_STORE_DIR, exist_ok=True)
        with open(_TICKETS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception:
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
            "latest_intent": (tracker.latest_message.get("intent") or {}).get("name"),
            "timestamp": int(time.time()),
            "slots": tracker.current_slot_values(),
            "metadata": (tracker.latest_message or {}).get("metadata") or {},
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
            # 🧾 Texto base técnico para pasarlo por el LLM
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
            try:
                mensaje_llm = llm_summarize_with_ollama(texto_base, contexto_llm)
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

        # Nuevo: leemos tipo_soporte y campos adicionales del form
        tipo_soporte = (tracker.get_slot("tipo_soporte") or "interno").strip()
        cedula = (tracker.get_slot("cedula") or "").strip()
        motivo = (tracker.get_slot("motivo_soporte") or "").strip()
        prefer_contacto = (tracker.get_slot("prefer_contacto") or "").strip()
        phone = (tracker.get_slot("phone") or "").strip()
        soporte_mensaje = (tracker.get_slot("soporte_mensaje") or "").strip()

        # Lo que ya tenías
        nombre = (tracker.get_slot("nombre") or "").strip()
        email = (tracker.get_slot("email") or "").strip()
        mensaje_slot = (tracker.get_slot("mensaje") or "").strip()

        mensaje = mensaje_slot or soporte_mensaje

        if not (nombre and email and mensaje):
            dispatcher.utter_message(
                text="❌ Faltan datos para crear el ticket de soporte."
            )
            return []

        # Meta enriquecida (seguimos mandando todos los slots)
        meta = {
            "rasa_sender_id": tracker.sender_id,
            "latest_intent": (tracker.latest_message.get("intent") or {}).get("name"),
            "timestamp": int(time.time()),
            "slots": tracker.current_slot_values(),
            "metadata": (tracker.latest_message or {}).get("metadata") or {},
        }

        # 🎯 Asunto y payload diferenciados según tipo_soporte
        if tipo_soporte == "pqrs":
            subject = "PQRS - Soporte técnico (Rasa)"
        else:
            subject = "Soporte técnico (Rasa)"

        payload = {
            "name": nombre,
            "email": email,
            "subject": subject,
            "message": mensaje,
            "conversation_id": tracker.sender_id,
            "tipo_soporte": tipo_soporte,       # 👈 nuevo
            "cedula": cedula,                   # 👈 nuevo
            "motivo_soporte": motivo,           # 👈 nuevo
            "prefer_contacto": prefer_contacto, # 👈 nuevo
            "phone": phone,                     # 👈 nuevo
            "metadata": meta,
        }

        headers = {"Content-Type": "application/json"}
        if HELPDESK_TOKEN:
            headers["Authorization"] = f"Bearer {HELPDESK_TOKEN}"

        resp = post_json_with_retries(HELPDESK_WEBHOOK, payload, headers)
        ok = bool(resp and 200 <= getattr(resp, "status_code", 0) < 300)

        jlog(
            logging.INFO,
            "action_soporte_submit",
            ok=ok,
            status_code=getattr(resp, "status_code", None),
        )

        # 🔁 Mantenemos tu lógica de reseteo de slots
        events: List[EventType] = [
            SlotSet("nombre", None),
            SlotSet("email", None),
            SlotSet("mensaje", None),
            SlotSet("soporte_mensaje", None),
            SlotSet("tipo_soporte", None),
        ]

        if ok:
            # 🧾 Construimos un texto base sin datos sensibles explícitos
            resumen_motivo = motivo or "soporte general"
            resumen_mensaje = (mensaje or "").strip()
            if len(resumen_mensaje) > 400:
                resumen_mensaje = resumen_mensaje[:400].rstrip() + "…"

            if tipo_soporte == "pqrs":
                texto_base = (
                    "He registrado tu caso como **PQRS formal** para el equipo de soporte. "
                    "Un asesor revisará tu solicitud y te contactará con la información que registraste.\n\n"
                    f"Motivo principal: {resumen_motivo}\n"
                    f"Descripción del problema: {resumen_mensaje}"
                )
            else:
                texto_base = (
                    "He registrado tu solicitud de **soporte interno** para la plataforma. "
                    "Un asesor la revisará y se comunicará contigo según tu preferencia de contacto.\n\n"
                    f"Motivo principal: {resumen_motivo}\n"
                    f"Descripción del problema: {resumen_mensaje}"
                )

            contexto_llm = {
                "flujo": "soporte_tecnico",
                "tipo_soporte": tipo_soporte,
                "motivo_soporte": resumen_motivo,
                "prefer_contacto": prefer_contacto or "no_especificado",
            }

            # ✨ Pasamos el texto por el LLM solo para mejorar redacción
            mensaje_final = llm_summarize_with_ollama(texto_base, contexto_llm)

            dispatcher.utter_message(text=mensaje_final)

            # Lógica de handoff / encuesta se mantiene igual
            if tracker.get_slot("escalar_humano"):
                events.append(FollowupAction("action_derivar_y_registrar_humano"))
            else:
                dispatcher.utter_message(response="utter_preguntar_satisfaccion")

            # Siempre reseteamos el flag de handoff
            events.append(SlotSet("escalar_humano", False))
            return events

        # ❌ Si NO se pudo registrar el soporte, no usamos LLM: mensaje directo y claro
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
        # Aquí podrías reutilizar HELPDESK_WEBHOOK o un webhook diferente para tutores.
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


class ActionDerivarYRegistrarHumano(Action):
    def name(self) -> Text:
        return "action_derivar_y_registrar_humano"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        dispatcher.utter_message(text="Te conecto con un agente humano en breve.")
        # Aquí podrías registrar el traspaso en tu backend si lo deseas.
        return []


class ActionProcesarSoporte(Action):
    def name(self) -> Text:
        return "action_procesar_soporte"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Aquí podrías guardar el ticket, enviar correo, etc.
        # Por ahora no hace nada "peligroso".
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
