# rasa/actions/acciones_academico.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Text
import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

from .common import _is_auth, _backend_base, _auth_headers

class ActionEstadoEstudiante(Action):
    def name(self) -> Text:
        return "action_estado_estudiante"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List:
        if not _is_auth(tracker):
            dispatcher.utter_message(response="utter_need_auth")
            return []
        estado: Optional[str] = None
        base = _backend_base()
        if base:
            try:
                resp = requests.get(f"{base}/api/estado-estudiante", headers=_auth_headers(tracker), timeout=8)
                if resp.ok:
                    data = resp.json()
                    estado = data.get("estado") if isinstance(data, dict) else None
            except Exception:
                pass
        if not estado:
            estado = "Activo (demo)"
        dispatcher.utter_message(text=f"✅ Tu estado académico es: {estado}.")
        return []

class ActionTutorAsignado(Action):
    def name(self) -> Text:
        return "action_tutor_asignado"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict]:
        if not _is_auth(tracker):
            dispatcher.utter_message(response="utter_need_auth")
            return []
        base = _backend_base()
        tutor_nombre: Optional[str] = None
        tutor_contacto: Optional[str] = None
        if base:
            try:
                resp = requests.get(f"{base}/api/tutor", headers=_auth_headers(tracker), timeout=8)
                if resp.ok:
                    data = resp.json() if isinstance(resp.json(), dict) else {}
                    tutor_nombre = data.get("nombre"); tutor_contacto = data.get("contacto")
            except Exception:
                pass
        if not tutor_nombre:
            tutor_nombre = "Ing. María Pérez (demo)"
        if not tutor_contacto:
            tutor_contacto = "maria.perez@zajuna.edu (demo)"
        dispatcher.utter_message(text=f"👩‍🏫 Tu tutor asignado es {tutor_nombre}. Contacto: {tutor_contacto}.")
        return []

class ActionListarCertificados(Action):
    def name(self) -> Text:
        return "action_listar_certificados"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if not _is_auth(tracker):
            dispatcher.utter_message(response="utter_need_auth")
            return []
        base_url = _backend_base()
        certificados: Optional[List[Dict[str, Any]]] = None
        if base_url:
            try:
                resp = requests.get(f"{base_url}/api/certificados", headers=_auth_headers(tracker), timeout=8)
                if resp.ok:
                    data = resp.json()
                    certificados = data.get("certificados") if isinstance(data, dict) else data
            except Exception:
                pass
        if not certificados:
            certificados = [
                {"curso": "Excel Intermedio", "fecha": "2025-06-10", "url": "https://zajuna.example/cert/123"},
                {"curso": "Programación Básica", "fecha": "2025-04-02", "url": "https://zajuna.example/cert/456"},
            ]
        lines = [f"• {i.get('curso','Certificado')} ({i.get('fecha','s.f.')})" + (f" → {i.get('url')}" if i.get('url') else "") for i in certificados]
        dispatcher.utter_message(text="🧾 Tus certificados:\n" + "\n".join(lines))
        return []

class ActionVerCertificados(Action):
    def name(self) -> Text:
        return "action_ver_certificados"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict]:
        if not _is_auth(tracker):
            dispatcher.utter_message(response="utter_need_auth")
            return []
        base = _backend_base()
        certificados: Optional[List[Dict[str, Any]]] = None
        if base:
            try:
                resp = requests.get(f"{base}/api/certificados", headers=_auth_headers(tracker), timeout=8)
                if resp.ok:
                    data = resp.json()
                    certificados = data.get("certificados") if isinstance(data, dict) else data
            except Exception:
                pass
        if not certificados:
            certificados = [
                {"curso": "Excel Intermedio", "fecha": "2025-06-10", "url": "https://zajuna.example/cert/123"},
                {"curso": "Programación Básica", "fecha": "2025-04-02", "url": "https://zajuna.example/cert/456"},
            ]
        lines = [f"• {i.get('curso','Certificado')} ({i.get('fecha','s.f.')})" + (f" → {i.get('url')}" if i.get('url') else "") for i in certificados]
        dispatcher.utter_message(text="🧾 Tus certificados:\n" + "\n".join(lines))
        return []

class ActionIngresoZajuna(Action):
    def name(self) -> str:
        return "action_ingreso_zajuna"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        dispatcher.utter_message(text="Perfecto, vamos a iniciar sesión. Por favor ingresa tus credenciales.")
        return []

class ActionRecuperarContrasena(Action):
    def name(self) -> str:
        return "action_recuperar_contrasena"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        dispatcher.utter_message(text="No hay problema. Te ayudaré a recuperar tu contraseña. Por favor sigue el enlace que te enviaré.")
        return []
