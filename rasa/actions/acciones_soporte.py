# ruta: rasa/actions/acciones_soporte.py
from __future__ import annotations

import logging
import time
import os
import json
import datetime
import traceback
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
from .core.llm_engine import run_llm
from .utils_logging import get_logger
from .core.nlp_utils import build_llm_request
from rasa_sdk.events import (
    ActiveLoop,
)
from .acciones_academico import validar_autenticacion

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


# ================================================================
# CATÁLOGO CENTRAL DE ACCIONES DE SOPORTE
# ================================================================

ACCIONES_SOPORTE = {

    "hablar_asesor": {
        "backend": None,
        "requires_auth": True,
        "proceso": "hablar_asesor",
        "resume_action": "action_solicitar_humano",
    },

    "contactar_tutor": {
        "backend": None,
        "requires_auth": True,
        "proceso": "contactar_tutor",
        "resume_action": "action_contactar_tutor",
    },

    "pqrsd": {
        "backend": None,
        "requires_auth": False,
        "proceso": "pqrsd",
    },

    "preguntas_frecuentes": {
        "backend": None,
        "requires_auth": False,
        "proceso": "preguntas_frecuentes",
    },

    "recuperar_contrasena": {
        "backend": None,
        "requires_auth": False,
        "proceso": "recuperar_contrasena",
    },

    "crear_caso":{
       "backend": None,      
       "requires_auth": True,
       "proceso":"crear_caso",
       "resume_action": "action_iniciar_soporte",
    },

}
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


class ActionIniciarSoporte(Action):

    def name(self) -> Text:
        return "action_iniciar_soporte"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        llm_request = build_llm_request(
            instruction="",
            macroflujo="support",
            subflujo="ticket",
            requires_auth=True,
            pending_action="crear_caso",
        )

        auth = validar_autenticacion(
            tracker,
            "crear_caso",
            llm_request,
        )

        if auth:
            return auth

        return [

            SlotSet(
                "proceso_activo",
                "crear_caso",
            ),

            SlotSet(
                "pending_action",
                None,
            ),

            FollowupAction(
                "action_autosave_snapshot",
            ),
            
            FollowupAction(
                "soporte_form",
            ),

        ]

class ActionSolicitarHumano(Action):

    def name(self) -> Text:
        return "action_solicitar_humano"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        llm_request = build_llm_request(

            instruction=(
                "Explica al estudiante que en el entorno de producción podrá "
                "solicitar atención de un asesor humano. Indica que primero debe "
                "autenticarse en la plataforma institucional y que, una vez validado "
                "el token JWT, el sistema permitirá generar la solicitud para ser "
                "atendido por un asesor. En esta versión del proyecto se demuestra "
                "el flujo de integración, pero la conexión definitiva depende de "
                "los servicios institucionales."
            ),

            macroflujo="support",

            subflujo="hablar_asesor",

            requires_auth=True,

            pending_action="hablar_asesor",

            next_action="action_ofrecer_continuar_soporte",

            fallback=(
                "El proceso para contactar un asesor quedó explicado correctamente."
            ),

        )

        auth = validar_autenticacion(
            tracker,
            "hablar_asesor",
            llm_request,
        )

        if auth:
            return auth

        return [

            SlotSet(
                "proceso_activo",
                "hablar_asesor",
            ),

            SlotSet(
                "pending_action",
                None,
            ),

            SlotSet(
                "llm_request",
                llm_request,
            ),

            FollowupAction(
                "action_handle_with_llm",
            ),

        ]

class ActionContactarTutor(Action):

    def name(self) -> Text:
        return "action_contactar_tutor"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        llm_request = build_llm_request(
            instruction="",
            macroflujo="support",
            subflujo="correo",
            requires_auth=True,
            pending_action="contactar_tutor",
        )

        auth = validar_autenticacion(
            tracker,
            "contactar_tutor",
            llm_request,
        )

        if auth:
            return auth

        llm_request.update(
            {
                "instruction": (
                    "Explica cómo funciona el contacto con el tutor académico. "
                    "Indica que el estudiante debe autenticarse y que posteriormente "
                    "el sistema podrá consultar el tutor asignado y generar el contacto "
                    "utilizando los servicios institucionales. En esta demostración "
                    "únicamente se presenta el flujo funcional."
                ),
                "next_action": "action_ofrecer_continuar_soporte",
                "fallback": (
                    "Se explicó el proceso para contactar al tutor."
                ),
            }
        )

        return [

            SlotSet(
                "proceso_activo",
                "contactar_tutor",
            ),

            SlotSet(
                "pending_action",
                None,
            ),

            SlotSet(
                "llm_request",
                llm_request,
            ),

            FollowupAction(
                "action_handle_with_llm",
            ),

        ]

class ActionRecuperarContrasena(Action):

    def name(self):
        return "action_recuperar_contrasena"

    def run(self, dispatcher, tracker, domain):

        request = build_llm_request(

            instruction=(
                "Explica paso a paso cómo recuperar la contraseña de acceso a "
                "la plataforma Zajuna. Indica que el estudiante debe utilizar "
                "la opción '¿Olvidó su contraseña?', ingresar su correo "
                "institucional y seguir el enlace enviado al correo para crear "
                "una nueva contraseña. Aclara que este proceso depende de la "
                "infraestructura institucional y que en esta versión del proyecto "
                "se demuestra únicamente el flujo."
            ),

            macroflujo="support",
            subflujo="recuperar_contrasena",
            requires_auth=False,
            next_action="action_ofrecer_continuar_soporte",
            fallback=(
                "Se explicó el procedimiento para recuperar la contraseña."
            ),

        )

        return [

            SlotSet(
                "proceso_activo",
                "recuperar_contrasena",
            ),

            SlotSet(
                "llm_request",
                request,
            ),

            FollowupAction(
                "action_handle_with_llm",
            ),

        ]


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

            return [

                SlotSet(
                    "llm_request",
                    {
                        "flow": "support",

                        "instruction":
                            (
                                "Agradece al estudiante por reportar el problema. "
                                "Indica que el ticket fue registrado correctamente y "
                                "que un agente revisará el caso y lo contactará por el "
                                "medio registrado. Si el caso es urgente, menciona "
                                "que puede utilizar los canales oficiales de soporte."
                            ),

                        "context":
                        {
                            "flujo": "support",
                            "correo_valido": bool(email),
                        },

                        "fallback":
                            (
                                 "✅ Tu solicitud fue registrada correctamente. "
                                 "Un agente revisará el caso."
                            ),
                    },
                ),

               FollowupAction(
                   "action_handle_with_llm"
               ),
            ]
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

            events.append(

                SlotSet(
                    "llm_request",
                    {
                        "instruction": texto_base,

                        "context":
                        {
                            "flujo": "support",
                            "tipo_soporte": tipo_soporte,
                            "motivo": resumen_motivo,
                            "prefer_contacto": (
                                prefer_contacto or "no_especificado"
                            ),
                        },

                        "fallback":
                            (
                                "✅ Tu solicitud fue registrada correctamente. "
                                "Un asesor revisará el caso."
                            )
                    }
                )
            )

            events.append(
                FollowupAction(
                    "action_handle_with_llm"
                )
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


class ActionRecuperarContrasena(Action):

    def name(self):
        return "action_recuperar_contrasena"

    def run(self, dispatcher, tracker, domain):

        request = build_llm_request(

            instruction=(
                "Explica paso a paso cómo recuperar la contraseña de acceso a "
                "la plataforma Zajuna. Indica que el estudiante debe utilizar "
                "la opción '¿Olvidó su contraseña?', ingresar su correo "
                "institucional y seguir el enlace enviado al correo para crear "
                "una nueva contraseña. Aclara que este proceso depende de la "
                "infraestructura institucional y que en esta versión del proyecto "
                "se demuestra únicamente el flujo."
            ),

            macroflujo="support",

            subflujo="recuperar_contrasena",

            requires_auth=False,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(
                "Se explicó el procedimiento para recuperar la contraseña."
            ),

        )

        return [

            SlotSet(
                "proceso_activo",
                "recuperar_contrasena",
            ),

            SlotSet(
                "llm_request",
                request,
            ),

            FollowupAction(
                "action_handle_with_llm",
            ),

        ]

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

class ActionPQRSDLLM(Action):
    """
    Envía al LLM la descripción del usuario para que redacte una
    PQRSD formal.
    """

    def name(self) -> Text:
        return "action_pqrsd_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        intent = tracker.get_intent_of_latest_message()

        logger.warning("=" * 80)
        logger.warning("[PQRSD ACTION] Entró ActionPQRSDLLM")
        logger.warning("=" * 80)

        logger.info("=" * 80)
        logger.info("[PQRSD] ActionPQRSDLLM")
        logger.info("texto=%s", tracker.latest_message.get("text"))
        logger.info("=" * 80)

        descripcion = (
            tracker.latest_message.get("text") or ""
        ).strip()

        if len(descripcion) < 5:

            dispatcher.utter_message(
                text=(
                    "No logré comprender la descripción de tu solicitud. "
                    "¿Podrías escribirla nuevamente con un poco más de detalle?"
                )
            )

            return []

        tipo = (
            tracker.get_slot("tipo_pqrsd")
            or "PQRSD"
        )

        instruction = (
            f"Tipo de solicitud: {tipo}\n\n"
            f"Descripción del usuario:\n{descripcion}"
        )

        eventos = [

            ActiveLoop(None),

            SlotSet(
                "requested_slot",
                None,
            ),

            SlotSet(
                "esperando_pqrsd",
                False,
            ),

            SlotSet(
                "proceso_activo",
                "pqrsd",
            ),

            SlotSet(
                "tema_consulta",
                descripcion,
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                 False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        eventos.extend(

            [
                SlotSet(
                    "tema_actual",
                    descripcion,
                ),

            ]

        )

        if intent != "radicar_pqrsd":

            eventos.extend(
                [
                    SlotSet(
                        "tema_actual",
                        descripcion,
                    ),
                ]
            )

        request = build_llm_request(

            instruction=instruction,

            macroflujo="support",

            subflujo="pqrsd",

            requires_auth=False,

            next_action="action_ofrecer_radicar_pqrsd",

        )
        logger.info(
            "[PQRSD] llm_request=%s",
            request,
        )
        logger.warning("=" * 80)
        logger.warning("[PQRSD] REQUEST CONSTRUIDO")
        logger.warning("REQUEST CONSTRUIDO = %s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )
        )

        eventos.append(
            FollowupAction(
                "action_handle_with_llm"
           )

        )

        logger.info(
            "Eventos que retorna ActionPQRSDLLM:"
        )

        logger.warning("=" * 80)
        logger.warning("[PQRSD] EVENTOS A RETORNAR")
        logger.warning("EVENTOS = %s", eventos)
        logger.warning("=" * 80)

        for evento in eventos:
            logger.info("  %s", evento)

        return eventos


class ActionOfrecerContinuarFaq(Action):

    def name(self) -> Text:
        return "action_ofrecer_continuar_faq"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.warning(
            "[CONTINUAR_FAQ] proceso=%s llm=%s",
            tracker.get_slot("proceso_activo"),
            tracker.get_slot("llm_request"),
        )

        dispatcher.utter_message(
            response="utter_ofrecer_continuar_faq"
        )

        esperando = tracker.get_slot(
            "esperando_decision_post_resolucion"
        )

        logger.warning(
            "[CONTINUAR_FAQ] esperando_decision_post_resolucion=%s",
            esperando,
        )

        if esperando:

            logger.warning(
                "[CONTINUAR_FAQ] Manteniendo espera post resolución"
            )

            return []

        logger.warning(
            "[CONTINUAR_FAQ] Flujo FAQ normal"
        )
        logger.warning(
            "[CONTINUAR_FAQ] esperando_pregunta_faq=%s",
            tracker.get_slot("esperando_pregunta_faq"),
        )
        return [

           SlotSet(
               "esperando_pregunta_faq",
               False,
           ), 
            
            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),


             SlotSet(
                 "proceso_activo",
                 "faq",
             ),

             SlotSet(
                 "confirmacion_cierre",
                 "pendiente",
             ),

        ]


class ActionOfrecerRadicarPQRSD(Action):

    def name(self) -> Text:
        return "action_ofrecer_radicar_pqrsd"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        dispatcher.utter_message(
            text=(
                "✅ La PQRSD ha sido redactada correctamente.\n\n"
            )
        )
        dispatcher.utter_message(
            text=(
                "Ahora puedes radicarla por los canales oficiales del SENA.\n\n"

                "Pasos para radicarla:\n\n"

                "1. Ingresa al Portal PQRSD del SENA:\n"
                "https://sciudadanos.sena.edu.co/\n\n"

                "2. Selecciona el tipo de usuario "
                "(Ciudadano o Anónimo).\n\n"

                "3. Copia y pega el texto generado por el asistente.\n\n"

                "4. Completa la información solicitada.\n\n"

                "5. Adjunta evidencias si cuentas con ellas "
                "(capturas de pantalla, documentos, etc.).\n\n"

                "6. Envía la solicitud y conserva el número de radicado para realizar seguimiento.\n\n"

                "Si el inconveniente está relacionado con la plataforma Zajuna, "
                "también puedes consultar:\n"
                "https://zajuna.sena.edu.co/soporte.php"
            )
        )

        dispatcher.utter_message(
            response="utter_ofrecer_continuar_pqrsd"
        )

        esperando = tracker.get_slot(
            "esperando_decision_post_resolucion"
        )

        logger.warning(
            "[CONTINUAR_PQRSD] esperando_decision_post_resolucion=%s",
            esperando,
        )

        if esperando:

            logger.warning(
                "[CONTINUAR_PQRSD] Manteniendo espera post resolución"
            )

            return []

        logger.warning(
            "[CONTINUAR_PQRSD] Flujo PQRSD normal"
        )

        return [

            SlotSet(
                "esperando_pqrsd",
                False,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "proceso_activo",
                "pqrsd",
            ),

            SlotSet("confirmacion_cierre", None)

        ]

class ActionPreguntasFrecuentesLLM(Action):

    def name(self) -> Text:
        return "action_preguntas_frecuentes_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        
        # ==========================================================
        # PROTECCIÓN DE FLUJO PQRSD
        # ==========================================================

        if (
             tracker.get_slot("proceso_activo") == "pqrsd"
             and tracker.get_slot("esperando_pqrsd")
        ):

             logger.warning(
                 "[FAQ] Mensaje ignorado. El usuario continúa redactando una PQRSD."
             )

             return []
        
        intent = tracker.get_intent_of_latest_message()

        logger.warning("=" * 80)
        logger.warning("[FAQ STATE - ENTRADA ActionPreguntasFrecuentesLLM]")
        logger.warning(
            "intent=%s",
            tracker.get_intent_of_latest_message(),
        )
        logger.warning(
            "texto=%s",
            tracker.latest_message.get("text"),
        )
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "esperando_pregunta_faq=%s",
            tracker.get_slot("esperando_pregunta_faq"),
        )
        logger.warning(
            "esperando_decision_post_resolucion=%s",
            tracker.get_slot("esperando_decision_post_resolucion"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)
        logger.error(
            "########## ENTRÉ A ActionPreguntasFrecuentesLLM ##########"
        )
        logger.info("=" * 80)
        logger.info("[SOPORTE] ActionPreguntasFrecuentesLLM")
        logger.info("texto=%s", tracker.latest_message.get("text"))
        logger.info("intent=%s", intent)
        logger.info("=" * 80)

        logger.warning(
            "[TRACE][FAQ] llm_request al entrar=%s",
            tracker.get_slot("llm_request"),
        )
        
        pregunta = (
            tracker.latest_message.get("text") or ""
        ).strip()


        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "esperando_pregunta_faq", 
                False,
            ),

            SlotSet("proceso_activo", "faq"),

            SlotSet("tema_consulta", pregunta),

            SlotSet("auth_login_form", None),

            SlotSet(
                "esperando_decision_post_resolucion",
                 False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        if intent != "continuar_faq":

            eventos.extend(

                [

                    SlotSet(
                        "tema_actual",
                        pregunta,
                    ),

                ]

            )

        request = build_llm_request(

            instruction=pregunta,

            macroflujo="support",

            subflujo="faq",

            requires_auth=False,

            next_action="action_ofrecer_continuar_faq",

        )

        logger.info(
            "[SOPORTE] llm_request=%s",
            request,
        )
        logger.warning("=" * 80)
        logger.warning("[FAQ] REQUEST CONSTRUIDO")
        logger.warning("%s", request)
        logger.warning("=" * 80)


        eventos.append(
            SlotSet(
                "llm_request",
                request,
            )
        )

        eventos.append(
            FollowupAction(
                "action_handle_with_llm"
            )
        )

        logger.info(
            "Eventos que retorna ActionPreguntasFrecuentesLLM:"
        )

        for e in eventos:
            logger.info("  %s", e)

        logger.error("=" * 80)
        logger.error("[FAQ] REQUEST FINAL")
        logger.error("%s", request)
        logger.error("=" * 80)
            
            
        return eventos
        

class ActionSolicitarPreguntaFAQ(Action):

    def name(self):
        return "action_solicitar_pregunta_faq"

    def run(self, dispatcher, tracker, domain):

        logger.error("EVENTOS DEL TRACKER:")
        for e in tracker.events[-15:]:
            logger.error(e)

        logger.error("===== STACK =====")
        logger.error("".join(traceback.format_stack()))
        logger.error("=================")
        
        logger.error("=" * 80)
        logger.error("[FAQ] ActionSolicitarPreguntaFAQ EJECUTADA")
        logger.error("intent=%s", tracker.get_intent_of_latest_message())
        logger.error("texto=%s", tracker.latest_message.get("text"))
        logger.error("proceso=%s", tracker.get_slot("proceso_activo"))
        logger.error("=" * 80)
        
        logger.warning(
            "[TRACE][ActionSolicitarPreguntaFAQ] llm_request al entrar=%s",
            tracker.get_slot("llm_request"),
        )

        logger.info(
            "[SOPORTE] Activando espera de pregunta FAQ"
        )

        dispatcher.utter_message(
            response="utter_solicitar_pregunta_faq"
        )

        logger.warning("=" * 80)
        logger.warning("[FAQ STATE - SALIDA ActionSolicitarPreguntaFAQ]")
        logger.warning(
            "esperando_pregunta_faq=True"
        )
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning("=" * 80)


        return [

            SlotSet(
                "llm_request",
                None,
            ),
            SlotSet(
                "esperando_pregunta_faq",
                False,
            ),

            SlotSet("tema_actual", None),
            SlotSet("tema_consulta", None),
            SlotSet("ultima_respuesta_llm", None),

            SlotSet(
                "proceso_activo",
                "faq",
            ),

        ]

class ActionSolicitarPQRSD(Action):

    def name(self) -> Text:
        return "action_solicitar_pqrsd"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.error("########## ENTRÓ ACTION_SOLICITAR_PQRSD ##########")
        
        logger.warning(
            "[TRACE][ActionSolicitarPQRSD] llm_request al entrar=%s",
            tracker.get_slot("llm_request"),
        )

        logger.info(
            "[SOPORTE] Activando espera de descripción PQRSD"
        )

        dispatcher.utter_message(
            response="utter_solicitar_pqrsd"
        )
        eventos = [

            SlotSet(
                "llm_request",
                None,
            ),
            SlotSet(
                "esperando_pqrsd",
                False,
            ),
            SlotSet(
                "proceso_activo",
                "pqrsd",
            ),

            SlotSet("tema_actual", None),
            SlotSet("tema_consulta", None),
            SlotSet("ultima_respuesta_llm", None),

        ]
        logger.error("########## SALE ACTION_SOLICITAR_PQRSD ##########")
        logger.error("Eventos=%s", eventos)

        return eventos

class ActionCrearCasoLLM(Action):

    def name(self) -> Text:
        return "action_crear_caso_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionCrearCasoLLM ejecutada.")

        logger.warning("=" * 80)
        logger.warning("[CREAR CASO - ENTRADA]")
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "proceso_activo",
                "crear_caso",
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        request = build_llm_request(

            instruction=(

                "Explica que la creación de un caso de soporte requiere "
                "autenticación institucional para asociar correctamente la "
                "solicitud al estudiante. Después del inicio de sesión se "
                "abrirá el formulario para registrar el caso de soporte."

            ),

            macroflujo="support",

            subflujo="crear_caso",

            requires_auth=True,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(

                "Esta funcionalidad requiere autenticación institucional."

            ),

        )

        logger.warning("=" * 80)
        logger.warning("[CREAR CASO] REQUEST")
        logger.warning("%s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        eventos.append(

            FollowupAction(
                "action_handle_with_llm",
            )

        )

        logger.info("Eventos ActionCrearCasoLLM:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos


class ActionHablarAsesorLLM(Action):

    def name(self) -> Text:
        return "action_hablar_asesor_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionHablarAsesorLLMM ejecutada.")

        logger.warning("=" * 80)
        logger.warning("[HABLAR ASESOR - ENTRADA]")
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "proceso_activo",
                "hablar_asesor",
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        request = build_llm_request(

            instruction=(

                "Explica que la creación de un caso de soporte requiere "
                "autenticación institucional para asociar correctamente la "
                "solicitud al estudiante. Después del inicio de sesión se "
                "abrirá el formulario para registrar el caso de soporte."

            ),

            macroflujo="support",

            subflujo="hablar_asesor",

            requires_auth=True,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(

                "Esta funcionalidad requiere autenticación institucional."

            ),

        )

        logger.warning("=" * 80)
        logger.warning("[HABLAR ASESOR] REQUEST")
        logger.warning("%s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        eventos.append(

            FollowupAction(
                "action_handle_with_llm",
            )

        )

        logger.info("Eventos ActionHablarAsesorLLM:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos


class ActionContactarTutorLLM(Action):

    def name(self) -> Text:
        return "action_contactar_tutor_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionContactarTutorLLM ejecutada.")

        logger.warning("=" * 80)
        logger.warning("[COMTACTAR TUTOR - ENTRADA]")
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "proceso_activo",
                "contactar_tutor",
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        request = build_llm_request(

            instruction=(

                "Explica que la creación de un caso de soporte requiere "
                "autenticación institucional para asociar correctamente la "
                "solicitud al estudiante. Después del inicio de sesión se "
                "abrirá el formulario para registrar el caso de soporte."

            ),

            macroflujo="support",

            subflujo="contactar_tutor",

            requires_auth=True,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(

                "Esta funcionalidad requiere autenticación institucional."

            ),

        )

        logger.warning("=" * 80)
        logger.warning("[COMTACTAR TUTOR] REQUEST")
        logger.warning("%s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        eventos.append(

            FollowupAction(
                "action_handle_with_llm",
            )

        )

        logger.info("Eventos ActionContactarTutorLLM:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos


class ActionRecuperarContrasenaLLM(Action):

    def name(self) -> Text:
        return "action_recuperar_contrasena_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionRecuperarContrasenaLLM ejecutada.")

        logger.warning("=" * 80)
        logger.warning("[RECUPERAR CONTRASENA - ENTRADA]")
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "proceso_activo",
                "recuperar_contrasena",
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        request = build_llm_request(

            instruction=(

                    "Explica paso a paso cómo recuperar la contraseña de acceso "
                    "a la plataforma Zajuna utilizando la opción "
                    "'¿Olvidó su contraseña?'."

            ),

            macroflujo="support",

            subflujo="recuperar_contrasena",

            requires_auth=True,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(

                "Esta funcionalidad requiere autenticación institucional."

            ),

        )

        logger.warning("=" * 80)
        logger.warning("[RECUPERAR CONTRASENA] REQUEST")
        logger.warning("%s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        eventos.append(

            FollowupAction(
                "action_handle_with_llm",
            )

        )

        logger.info("Eventos ActionRecuperarContrasenaLLM:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos




class ActionConsultarEstadoLLM(Action):

    def name(self) -> Text:
        return "action_consultar_estado_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionConsultarEstadoLLM ejecutada.")

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR ESTADO - ENTRADA]")
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "proceso_activo",
                "consultar_estado",
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        request = build_llm_request(

            instruction=(

                "Explica que la creación de un caso de soporte requiere "
                "autenticación institucional para asociar correctamente la "
                "solicitud al estudiante. Después del inicio de sesión se "
                "abrirá el formulario para registrar el caso de soporte."

            ),

            macroflujo="support",

            subflujo="consultar_estado",

            requires_auth=True,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(

                "Esta funcionalidad requiere autenticación institucional."

            ),

        )

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR ESTADO] REQUEST")
        logger.warning("%s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        eventos.append(

            FollowupAction(
                "action_handle_with_llm",
            )

        )

        logger.info("Eventos ActionConsultarEstadoLLM:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos

class ActionConsultarTutorLLM(Action):

    def name(self) -> Text:
        return "action_consultar_tutor_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionConsultarTutorLLM ejecutada.")

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR TUTOR - ENTRADA]")
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "proceso_activo",
                "consultar_tutor",
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        request = build_llm_request(

            instruction=(

                "Explica que la creación de un caso de soporte requiere "
                "autenticación institucional para asociar correctamente la "
                "solicitud al estudiante. Después del inicio de sesión se "
                "abrirá el formulario para registrar el caso de soporte."

            ),

            macroflujo="support",

            subflujo="consultar_tutor",

            requires_auth=True,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(

                "Esta funcionalidad requiere autenticación institucional."

            ),

        )

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR TUTOR] REQUEST")
        logger.warning("%s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        eventos.append(

            FollowupAction(
                "action_handle_with_llm",
            )

        )

        logger.info("Eventos ActionConsultarTutorLLM:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos



class ActionConsultarHorariosLLM(Action):

    def name(self) -> Text:
        return "action_consultar_horarios_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionConsultarHorariosLLM ejecutada.")

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR HORARIOS - ENTRADA]")
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "proceso_activo",
                "consultar_horarios",
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        request = build_llm_request(

            instruction=(

                "Explica que la creación de un caso de soporte requiere "
                "autenticación institucional para asociar correctamente la "
                "solicitud al estudiante. Después del inicio de sesión se "
                "abrirá el formulario para registrar el caso de soporte."

            ),

            macroflujo="support",

            subflujo="consultar_horarios",

            requires_auth=True,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(

                "Esta funcionalidad requiere autenticación institucional."

            ),

        )

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR HORARIOS] REQUEST")
        logger.warning("%s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        eventos.append(

            FollowupAction(
                "action_handle_with_llm",
            )

        )

        logger.info("Eventos ActionConsultarHorariosLLM:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos

class ActionConsultarProgresoLLM(Action):

    def name(self) -> Text:
        return "action_consultar_progreso_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionConsultarProgresoLLM ejecutada.")

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR PROGRESO - ENTRADA]")
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "proceso_activo",
                "consultar_progreso",
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        request = build_llm_request(

            instruction=(

                "Explica que la creación de un caso de soporte requiere "
                "autenticación institucional para asociar correctamente la "
                "solicitud al estudiante. Después del inicio de sesión se "
                "abrirá el formulario para registrar el caso de soporte."

            ),

            macroflujo="support",

            subflujo="consultar_progreso",

            requires_auth=True,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(

                "Esta funcionalidad requiere autenticación institucional."

            ),

        )

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR PROGRESO] REQUEST")
        logger.warning("%s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        eventos.append(

            FollowupAction(
                "action_handle_with_llm",
            )

        )

        logger.info("Eventos ActionConsultarProgresoLLM:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos


class ActionConsultarHistorialLLM(Action):

    def name(self) -> Text:
        return "action_consultar_historial_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionConsultarHistorialLLM ejecutada.")

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR HISTORIAL - ENTRADA]")
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "proceso_activo",
                "consultar_historial",
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        request = build_llm_request(

            instruction=(

                "Explica que la creación de un caso de soporte requiere "
                "autenticación institucional para asociar correctamente la "
                "solicitud al estudiante. Después del inicio de sesión se "
                "abrirá el formulario para registrar el caso de soporte."

            ),

            macroflujo="support",

            subflujo="consultar_historial",

            requires_auth=True,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(

                "Esta funcionalidad requiere autenticación institucional."

            ),

        )

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR HISTORIAL] REQUEST")
        logger.warning("%s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        eventos.append(

            FollowupAction(
                "action_handle_with_llm",
            )

        )

        logger.info("Eventos ActionConsultarHistorialLLM:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos


class ActionConsultarCertificadosLLM(Action):

    def name(self) -> Text:
        return "action_consultar_certificados_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionConsultarCertificadosLLM ejecutada.")

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR CERTIFICADOS - ENTRADA]")
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "proceso_activo",
                "consultar_certificados",
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        request = build_llm_request(

            instruction=(

                "Explica que la creación de un caso de soporte requiere "
                "autenticación institucional para asociar correctamente la "
                "solicitud al estudiante. Después del inicio de sesión se "
                "abrirá el formulario para registrar el caso de soporte."

            ),

            macroflujo="support",

            subflujo="consultar_certificados",

            requires_auth=True,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(

                "Esta funcionalidad requiere autenticación institucional."

            ),

        )

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR CERTIFICADOS] REQUEST")
        logger.warning("%s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        eventos.append(

            FollowupAction(
                "action_handle_with_llm",
            )

        )

        logger.info("Eventos ActionConsultarCertificadosLLM:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos

class ActionConsultarPagosLLM(Action):

    def name(self) -> Text:
        return "action_consultar_pagos_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionConsultarPagosLLM ejecutada.")

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR PAGOS - ENTRADA]")
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "proceso_activo",
                "consultar_pagos",
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        request = build_llm_request(

            instruction=(

                "Explica que la creación de un caso de soporte requiere "
                "autenticación institucional para asociar correctamente la "
                "solicitud al estudiante. Después del inicio de sesión se "
                "abrirá el formulario para registrar el caso de soporte."

            ),

            macroflujo="support",

            subflujo="consultar_pagos",

            requires_auth=True,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(

                "Esta funcionalidad requiere autenticación institucional."

            ),

        )

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR PAGOS] REQUEST")
        logger.warning("%s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        eventos.append(

            FollowupAction(
                "action_handle_with_llm",
            )

        )

        logger.info("Eventos ActionConsultarPagosLLM:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos



class ActionConsultarNotasLLM(Action):

    def name(self) -> Text:
        return "action_consultar_notas_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionConsultar_NotasLLM ejecutada.")

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR NOTAS - ENTRADA]")
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "proceso_activo",
                "consultar_notas",
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        request = build_llm_request(

            instruction=(

                "Explica que la creación de un caso de soporte requiere "
                "autenticación institucional para asociar correctamente la "
                "solicitud al estudiante. Después del inicio de sesión se "
                "abrirá el formulario para registrar el caso de soporte."

            ),

            macroflujo="support",

            subflujo="consultar_notas",

            requires_auth=True,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(

                "Esta funcionalidad requiere autenticación institucional."

            ),

        )

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR NOTAS] REQUEST")
        logger.warning("%s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        eventos.append(

            FollowupAction(
                "action_handle_with_llm",
            )

        )

        logger.info("Eventos ActionConsultarNotasLLM:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos


class ActionConsultarFichaLLM(Action):

    def name(self) -> Text:
        return "action_consultar_ficha_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionConsultarFichaLLM ejecutada.")

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR FICHA - ENTRADA]")
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "proceso_activo",
                "consultar_ficha",
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        request = build_llm_request(

            instruction=(

                "Explica que la creación de un caso de soporte requiere "
                "autenticación institucional para asociar correctamente la "
                "solicitud al estudiante. Después del inicio de sesión se "
                "abrirá el formulario para registrar el caso de soporte."

            ),

            macroflujo="support",

            subflujo="consultar_ficha",

            requires_auth=True,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(

                "Esta funcionalidad requiere autenticación institucional."

            ),

        )

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR FICHA] REQUEST")
        logger.warning("%s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        eventos.append(

            FollowupAction(
                "action_handle_with_llm",
            )

        )

        logger.info("Eventos ActionConsultarFichaLLM:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos


class ActionConsultarInscripcionesLLM(Action):

    def name(self) -> Text:
        return "action_consultar_inscripciones_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info("ActionConsultarInscripcionesLLM ejecutada.")

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR INSCRIPCIONE - ENTRADA]")
        logger.warning(
            "proceso_activo=%s",
            tracker.get_slot("proceso_activo"),
        )
        logger.warning(
            "llm_request=%s",
            tracker.get_slot("llm_request"),
        )
        logger.warning("=" * 80)

        eventos = [

            ActiveLoop(None),

            SlotSet("requested_slot", None),

            SlotSet(
                "proceso_activo",
                "consultar_inscripciones",
            ),

            SlotSet(
                "auth_login_form",
                None,
            ),

            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),

            SlotSet(
                "confirmacion_cierre",
                None,
            ),

        ]

        request = build_llm_request(

            instruction=(

                "Explica que la creación de un caso de soporte requiere "
                "autenticación institucional para asociar correctamente la "
                "solicitud al estudiante. Después del inicio de sesión se "
                "abrirá el formulario para registrar el caso de soporte."

            ),

            macroflujo="support",

            subflujo="consultar_inscripciones",

            requires_auth=True,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(

                "Esta funcionalidad requiere autenticación institucional."

            ),

        )

        logger.warning("=" * 80)
        logger.warning("[CONSULTAR INSCRIPCIONES] REQUEST")
        logger.warning("%s", request)
        logger.warning("=" * 80)

        eventos.append(

            SlotSet(
                "llm_request",
                request,
            )

        )

        eventos.append(

            FollowupAction(
                "action_handle_with_llm",
            )

        )

        logger.info("Eventos ActionConsultarInscripcionesLLM:")

        for e in eventos:
            logger.info("  %s", e)

        return eventos


class ActionOfrecerContinuarSoporte(Action):

    def name(self) -> Text:
        return "action_ofrecer_continuar_soporte"

    def run(
        self,
        dispatcher,
        tracker,
        domain,
    ) -> List[EventType]:

        dispatcher.utter_message(
            response="utter_ofrecer_continuar_proceso"
        )

        return [
            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),
            SlotSet("llm_request", None)
        ]

class ActionOfrecerContinuarAdministrativo(Action):

    def name(self) -> Text:
        return "action_ofrecer_continuar_administrativo"

    def run(
        self,
        dispatcher,
        tracker,
        domain,
    ) -> List[EventType]:

        dispatcher.utter_message(
            response="utter_ofrecer_continuar_administrativo"
        )

        return [
            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),
            SlotSet("llm_request", None)
        ]



class ActionLimpiarFaq(Action):

    def name(self) -> Text:
        return "action_limpiar_faq"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info(
            "[FAQ] Limpiando estado antes de nueva pregunta"
        )

        return [

            SlotSet(
                "llm_request",
                None,
            ),

            SlotSet(
                "ultima_respuesta_llm",
                None,
            ),

            SlotSet(
                "tema_actual",
                None,
            ),

            SlotSet(
                "tema_consulta",
                None,
            ),

            SlotSet(
                "esperando_pregunta_faq",
                True,
            ),

            SlotSet(
                "proceso_activo",
                "faq",
            ),

        ]

class ActionLimpiarPqrsd(Action):

    def name(self) -> Text:
        return "action_limpiar_pqrsd"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        logger.info(
            "[PQRSD] Limpiando estado para nueva radicación"
        )

        return [

            SlotSet(
                "llm_request",
                None,
            ),

            SlotSet(
                "ultima_respuesta_llm",
                None,
            ),

            SlotSet(
                "tema_actual",
                None,
            ),

            SlotSet(
                "tema_consulta",
                None,
            ),

            SlotSet(
                "esperando_pqrsd",
                True,
            ),

            SlotSet(
                "proceso_activo",
                "pqrsd",
            ),

        ]