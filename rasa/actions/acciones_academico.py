# ruta: rasa/actions/acciones_academico.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Text

import os
import logging
import requests

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import EventType

from .common import _is_auth, _backend_base, _auth_headers, _has_auth
from .acciones_llm import llm_summarize_with_ollama, build_auth_required_message_for_action
from .acciones_certificados import build_certificados_summary

logger = logging.getLogger(__name__)


# ======================
# 🎓 Estado del estudiante
# ======================
class ActionVerEstadoEstudiante(Action):
    def name(self) -> str:
        return "action_ver_estado_estudiante"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        # 1) Validar autenticación SIN LLM
        if not _is_auth(tracker):
            base_url = tracker.get_slot("zajuna_base_url") or "https://zajuna.edu"
            msg = build_auth_required_message_for_action(
                "consultar tu estado académico real",
                base_url,
            )
            dispatcher.utter_message(text=msg)
            return []

        estado: Optional[str] = None
        base = _backend_base()

        if base:
            try:
                resp = requests.get(
                    f"{base}/api/estado-estudiante",
                    headers=_auth_headers(tracker),
                    timeout=8,
                )
                if resp.ok:
                    estado = (resp.json() or {}).get("estado")
            except Exception:
                # Si la API falla, dejamos estado como None y usamos fallback
                logger.exception("Error consultando estado del estudiante en el backend.")
                pass

        estado_final = estado or "Activo (demo)"

        # 2) Mensaje factual directo (NO pasa por LLM)
        dispatcher.utter_message(
            text=f"✅ Tu estado académico es: {estado_final}."
        )

        # 3) Explicación adicional usando LLM (opcional, solo redacción)
        try:
            texto_base = (
                f"Tu estado académico actual en Zajuna es: {estado_final}. "
                "Explica brevemente qué significa este estado para el estudiante "
                "y menciona, de forma general, qué acciones podría tomar (por ejemplo, "
                "revisar sus cursos, contactar a soporte si ve algo raro, etc.)."
            )
            contexto_llm = {
                "flujo": "estado_estudiante",
                "estado": estado_final,
            }
            explicacion = llm_summarize_with_ollama(texto_base, contexto_llm)

            if explicacion and explicacion.strip() and explicacion.strip() != texto_base:
                dispatcher.utter_message(text=explicacion.strip())
        except Exception:
            # No rompemos la acción si algo falla con el LLM
            logger.exception("Error generando explicación LLM para estado del estudiante.")

        return []


# ======================
# 👩‍🏫 Tutor asignado
# ======================
class ActionTutorAsignado(Action):
    def name(self) -> Text:
        return "action_tutor_asignado"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        if not (_is_auth(tracker) or _has_auth(tracker)):
            dispatcher.utter_message(response="utter_pedir_autenticacion")
            return []

        base = _backend_base()
        nombre, contacto = None, None

        if base:
            try:
                resp = requests.get(
                    f"{base}/api/tutor",
                    headers=_auth_headers(tracker),
                    timeout=8,
                )
                if resp.ok:
                    data = resp.json()
                    if isinstance(data, dict):
                        nombre = data.get("nombre")
                        contacto = data.get("contacto")
            except Exception:
                # Aquí podrías loguear el error si quieres
                logger.exception("Error consultando tutor asignado en el backend.")
                pass

        # Valores por defecto si la API no devuelve nada
        nombre = nombre or "Ing. María Pérez (demo)"
        contacto = contacto or "maria.perez@zajuna.edu (demo)"

        dispatcher.utter_message(
            text=f"👩‍🏫 Tu tutor asignado es {nombre}. Contacto: {contacto}."
        )

        return []


# ======================
# 🎓 Certificados (listado resumido)
# ======================
class ActionListarCertificados(Action):
    def name(self) -> Text:
        return "action_listar_certificados"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        # 1) Revisar autenticación SIN LLM
        if not _is_auth(tracker):
            # Modo invitado: explicar cómo hacerlo desde la plataforma
            base_url = tracker.get_slot("zajuna_base_url") or "https://zajuna.edu"
            texto_base = (
                "Esta acción requiere que tengas sesión iniciada en la plataforma Zajuna "
                "para mostrarte tus certificados reales.\n\n"
                "👉 Pasos para consultar tus certificados directamente en Zajuna:\n"
                f"1) Ingresa a {base_url}/login\n"
                "2) Inicia sesión con tu usuario y contraseña.\n"
                "3) Ve al menú de certificados o historial académico.\n"
                "4) Allí podrás ver, descargar o imprimir tus certificados disponibles.\n\n"
                "Si quieres que el asistente te muestre un resumen personalizado aquí, "
                "primero inicia sesión en Zajuna y luego vuelve a escribir: "
                "\"consultar certificados\"."
            )

            contexto = {
                "flujo": "certificados_modo_invitado",
            }
            mensaje = llm_summarize_with_ollama(texto_base, contexto)
            dispatcher.utter_message(text=mensaje)

            # Mensaje estándar reutilizable de "requiere autenticación"
            msg = build_auth_required_message_for_action(
                "ver tus certificados personales",
                base_url,
            )
            dispatcher.utter_message(text=msg)
            return []

        # 2) Usuario autenticado → llamar al backend
        certificados: List[Dict[str, Any]] = []

        try:
            base_url = os.getenv("BACKEND_BASE_URL", "")
            if base_url:
                resp = requests.get(
                    f"{base_url}/api/certificados",
                    headers=_auth_headers(tracker),  # asumiendo que ya tienes este helper
                    timeout=10,
                )
                if resp.ok:
                    data = resp.json() or {}
                    # AJUSTA A TU ESQUEMA REAL
                    certificados = data.get("certificados", [])
        except Exception:
            logger.exception("Error al consultar certificados en el backend.")

        # Resumen técnico + mejora de redacción con LLM
        texto_base = build_certificados_summary(certificados)
        contexto_llm = {
            "flujo": "certificados",
            "cantidad_certificados": len(certificados),
        }

        mensaje = llm_summarize_with_ollama(texto_base, contexto_llm)

        dispatcher.utter_message(text=mensaje)
        return []


# ======================
# Wrappers con nombres "zajuna_*" (si los usas en otros rules/stories)
# ======================
class ZajunaGetCertificados(Action):
    def name(self) -> Text:
        return "zajuna_get_certificados"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        # Simplemente delega en ActionListarCertificados para mantener compatibilidad
        return ActionListarCertificados().run(dispatcher, tracker, domain)


class ZajunaGetEstadoEstudiante(Action):
    def name(self) -> Text:
        return "zajuna_get_estado_estudiante"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        # Delegamos en ActionVerEstadoEstudiante (nombre correcto de la clase)
        return ActionVerEstadoEstudiante().run(dispatcher, tracker, domain)
