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

    "solicitar_soporte": {
        "backend": None,
        "requires_auth": True,
        "proceso": "solicitar_soporte",
        "resume_action": "action_iniciar_soporte",
    },

    "hablar_asesor": {
        "backend": None,
        "requires_auth": True,
        "proceso": "hablar_asesor",
        "resume_action": "action_escalar_humano",
    },

    "contactar_tutor": {
        "backend": None,
        "requires_auth": True,
        "proceso": "contactar_tutor",
        "resume_action": "action_enviar_correo_tutor",
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
            instruction="",
            macroflujo="support",
            subflujo="asesor",
            requires_auth=True,
            pending_action="hablar_asesor",
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

             FollowupAction(
                 "action_autosave_snapshot",
             ),
            
            FollowupAction(
                "action_conectar_humano",
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

        return [

            SlotSet(
                "proceso_activo",
                "contactar_tutor",
            ),

            SlotSet(
                "pending_action",
                None,
            ),

            FollowupAction(
                "action_autosave_snapshot",
            ),
            
            FollowupAction(
                "action_enviar_correo_tutor",
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
                True,
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
                True,
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
                True,
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
                True,
            ),

            SlotSet("tema_actual", None),
            SlotSet("tema_consulta", None),
            SlotSet("ultima_respuesta_llm", None),

            SlotSet(
                "proceso_activo",
                "faq",
            ),

        ]

class ActionSoporteTecnicoLLM(Action):

    def name(self) -> Text:
        return "action_soporte_tecnico_llm"

    def run(
        self,
        dispatcher,
        tracker,
        domain,
    ) -> List[EventType]:

        logger.info("ActionSoporteTecnicoLLM ejecutada.")

        request = build_llm_request(

            instruction=(
                "Actúa como el asistente técnico de la plataforma Zajuna. "
                "Analiza el problema descrito por el estudiante y proporciona "
                "una guía clara y paso a paso para intentar resolverlo. "
                "Si el inconveniente no puede solucionarse mediante orientación, "
                "indica amablemente que el estudiante puede crear un caso de soporte "
                "o solicitar atención de un asesor humano."
            ),

            macroflujo="support",

            subflujo="soporte_tecnico",

            requires_auth=False,

            next_action="action_ofrecer_continuar_soporte",

            fallback=(
                "Estoy listo para ayudarte con tu problema técnico. "
                "Cuéntame qué inconveniente estás presentando."
            ),
        )

        return [

            SlotSet(
                "llm_request",
                request,
            ),

            FollowupAction(
                "action_handle_with_llm",
            ),

        ]


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
            response="utter_ofrecer_continuar_soporte"
        )

        return [
            SlotSet(
                "esperando_decision_post_resolucion",
                False,
            ),
            SlotSet("llm_request", None)
        ]


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