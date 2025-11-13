# rasa/actions/acciones_menu_estado_certificados.py

from __future__ import annotations
from typing import Any, Dict, List, Text, Optional

import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType

# Reutilizamos helpers si ya existen en tu proyecto
# (ajusta la ruta si tu archivo común se llama distinto)
from .common import _backend_base, _auth_headers


class ActionConsultarCertificados(Action):
    """
    Acción para manejar el intent `consultar_certificados` desde el menú.

    - Si el usuario NO está autenticado => muestra `utter_login_requerido`.
    - Si SÍ está autenticado:
        * Llama al backend /api/certificados (si `_backend_base()` devuelve URL),
        * O usa datos de ejemplo si el backend no responde,
        * Construye un listado en Markdown y llama a `utter_certificado_listado`
          pasando la variable `certificados_md`.
    """

    def name(self) -> Text:
        return "action_consultar_certificados"

    def _obtener_certificados_backend(
        self, tracker: Tracker
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Intenta obtener certificados reales desde el backend.
        Retorna una lista de dicts o None si falla.
        """
        base = _backend_base()
        if not base:
            return None

        try:
            resp = requests.get(
                f"{base}/api/certificados",
                headers=_auth_headers(tracker),
                timeout=8,
            )
            if not resp.ok:
                return None

            data = resp.json()
            # Soporta tanto:
            #   { "certificados": [...] }
            # como:
            #   [ {...}, {...} ]
            if isinstance(data, dict):
                return data.get("certificados") or []
            if isinstance(data, list):
                return data
            return None
        except Exception:
            return None

    def _certificados_demo(self) -> List[Dict[str, Any]]:
        """
        Certificados de ejemplo si el backend no responde.
        Puedes borrar o modificar este método para producción.
        """
        return [
            {
                "curso": "Excel Intermedio",
                "fecha": "2025-06-10",
                "url": "https://zajuna.example/cert/123",
            },
            {
                "curso": "Programación Básica",
                "fecha": "2025-04-02",
                "url": "https://zajuna.example/cert/456",
            },
        ]

    def _formatear_certificados_md(
        self, certificados: List[Dict[str, Any]]
    ) -> Text:
        """
        Convierte la lista de certificados en un bloque Markdown
        para usar en `utter_certificado_listado` como {certificados_md}.
        """
        if not certificados:
            return "No se encontraron certificados emitidos todavía."

        lineas: List[str] = []
        for c in certificados:
            curso = c.get("curso", "Certificado")
            fecha = c.get("fecha", "s.f.")
            url = c.get("url")

            if url:
                lineas.append(f"- 🎓 **{curso}** ({fecha}) → {url}")
            else:
                lineas.append(f"- 🎓 **{curso}** ({fecha})")

        return "\n".join(lineas)

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        # 1) Verificar si está autenticado
        is_auth = bool(tracker.get_slot("is_authenticated"))
        if not is_auth:
            # Reutiliza la respuesta definida en tu domain:
            #   utter_login_requerido  (en domain_menu_estado_certificados.yml)
            dispatcher.utter_message(response="utter_login_requerido")
            return []

        # 2) Intentar traer certificados reales desde backend
        certificados = self._obtener_certificados_backend(tracker)
        if certificados is None or len(certificados) == 0:
            certificados = self._certificados_demo()

        # 3) Formatear en Markdown para el template
        certificados_md = self._formatear_certificados_md(certificados)

        # 4) Usar la respuesta del domain:
        #   utter_certificado_listado:
        #     text: |
        #       📑 **Tus certificados**
        #       {certificados_md}
        dispatcher.utter_message(
            response="utter_certificado_listado",
            certificados_md=certificados_md,
        )

        return []
