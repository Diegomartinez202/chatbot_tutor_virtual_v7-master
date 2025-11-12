# ruta: rasa/actions/acciones_academico.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Text
import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

# Si tienes helpers centralizados, impórtalos aquí
# from .common import _is_auth, _backend_base, _auth_headers

# --------- Helpers mínimos para evitar import errors ---------
def _is_auth(tracker: Tracker) -> bool:
    v = tracker.get_slot("is_authenticated")
    return bool(v)

def _backend_base() -> Optional[str]:
    # Ajusta si tienes una URL configurada vía env
    return None

def _auth_headers(tracker: Tracker) -> Dict[str, str]:
    token = (tracker.get_slot("auth_token") or "").strip()
    return {"Authorization": f"Bearer {token}"} if token else {}

# ======================
# 📊 Estado estudiante
# ======================
class ActionEstadoEstudiante(Action):
    def name(self) -> Text: 
        return "action_estado_estudiante"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List:
        if not _is_auth(tracker):
            dispatcher.utter_message(response="utter_pedir_autenticacion")
            return []

        estado: Optional[str] = None
        base = _backend_base()
        if base:
            try:
                resp = requests.get(f"{base}/api/estado-estudiante", headers=_auth_headers(tracker), timeout=8)
                if resp.ok:
                    estado = (resp.json() or {}).get("estado")
            except Exception:
                pass

        dispatcher.utter_message(text=f"✅ Tu estado académico es: {estado or 'Activo (demo)'}." )
        return []

# ======================
# 👩‍🏫 Tutor asignado
# ======================
class ActionTutorAsignado(Action):
    def name(self) -> Text: 
        return "action_tutor_asignado"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict]:
        if not _is_auth(tracker):
            dispatcher.utter_message(response="utter_pedir_autenticacion")
            return []

        base = _backend_base()
        nombre, contacto = None, None
        if base:
            try:
                resp = requests.get(f"{base}/api/tutor", headers=_auth_headers(tracker), timeout=8)
                if resp.ok:
                    data = resp.json() if isinstance(resp.json(), dict) else {}
                    nombre, contacto = data.get("nombre"), data.get("contacto")
            except Exception:
                pass

        dispatcher.utter_message(
            text=f"👩‍🏫 Tu tutor asignado es {nombre or 'Ing. María Pérez (demo)'}."
                 f" Contacto: {contacto or 'maria.perez@zajuna.edu (demo)'}."
        )
        return []

# ======================
# 🎓 Certificados
# ======================
class ActionListarCertificados(Action):
    def name(self) -> Text: 
        return "action_listar_certificados"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if not _is_auth(tracker):
            dispatcher.utter_message(response="utter_pedir_autenticacion")
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

        lines = [
            f"• {i.get('curso','Certificado')} ({i.get('fecha','s.f.')})" + (f" → {i.get('url')}" if i.get('url') else "")
            for i in certificados
        ]
        dispatcher.utter_message(text="🧾 Tus certificados:\n" + "\n".join(lines))
        return []

class ActionVerCertificados(Action):
    def name(self) -> Text: 
        return "action_ver_certificados"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict]:
        return ActionListarCertificados().run(dispatcher, tracker, domain)

# ======================
# 🔐 Flujos simples login/recuperación (opcionales)
# ======================
class ActionIngresoZajuna(Action):
    def name(self) -> str: 
        return "action_ingreso_zajuna"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        dispatcher.utter_message(text="Perfecto, vamos a iniciar sesión. Por favor ingresa tus credenciales.")
        return []

class ActionRecuperarContrasena(Action):
    def name(self) -> str: 
        return "action_recuperar_contrasena"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        dispatcher.utter_message(text="Te ayudo a recuperar tu contraseña. Te enviaré un enlace al correo registrado.")
        return []

# ======================
# Wrappers con nombres "zajuna_*" (si los usas en otros rules/stories)
# ======================
class ZajunaGetCertificados(Action):
    def name(self) -> Text:
        return "zajuna_get_certificados"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict]:
        return ActionListarCertificados().run(dispatcher, tracker, domain)

class ZajunaGetEstadoEstudiante(Action):
    def name(self) -> Text:
        return "zajuna_get_estado_estudiante"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict]:
        return ActionEstadoEstudiante().run(dispatcher, tracker, domain)
