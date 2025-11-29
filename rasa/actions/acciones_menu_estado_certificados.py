# ruta: rasa/actions/acciones_menu_estado_certificados.py
from __future__ import annotations

from typing import Any, Dict, List, Text, Optional

import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType

from .common import _backend_base, _auth_headers, _has_auth
from .acciones_llm import llm_summarize_with_ollama


class ActionConsultarCertificados(Action):
    """
    Acción para manejar el intent `consultar_certificados` desde el menú.

    - Si el usuario NO está autenticado => muestra `utter_login_requerido`.
    - Si SÍ está autenticado:
        * Llama al backend /api/certificados (si `_backend_base()` devuelve URL),
        * O usa datos de ejemplo si el backend no responde,
        * Construye un listado en Markdown y llama a `utter_certificado_listado`
          pasando la variable `certificados_md`.
        * (Nuevo) Genera un pequeño resumen con Ollama, a partir de esos mismos datos.
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
            curso = c.get("curso") or c.get("nombre") or "Certificado"
            fecha = c.get("fecha") or c.get("fecha_emision") or "s.f."
            url = c.get("url") or c.get("ver_url") or c.get("link")

            if url:
                lineas.append(f"- 🎓 **{curso}** ({fecha}) → {url}")
            else:
                lineas.append(f"- 🎓 **{curso}** ({fecha})")

        return "\n".join(lineas)

    def _build_resumen_tecnico(self, certificados: List[Dict[str, Any]]) -> Text:
        """
        Construye un texto base 'técnico' a partir de la lista de certificados
        para que el LLM lo convierta en algo tipo:
        'Tienes 3 certificados destacados en ...'
        """
        if not certificados:
            return (
                "No se encontraron certificados emitidos todavía para este usuario. "
                "Explica de forma amable que aún no hay certificados disponibles y sugiere "
                "que revise más adelante o consulte con soporte si cree que falta alguno."
            )

        total = len(certificados)
        nombres = []
        for c in certificados[:5]:
            curso = c.get("curso") or c.get("nombre") or "un programa"
            nombres.append(curso)

        lista_nombres = ", ".join(nombres)

        texto_base = (
            f"Se encontraron {total} certificados para el usuario. "
            f"Algunos de los cursos asociados son: {lista_nombres}. "
            "Genera un mensaje claro y amable que resuma cuántos certificados tiene, "
            "resalte que se listarán a continuación y recuerde que puede descargarlos "
            "o consultarlos desde la plataforma Zajuna."
        )

        return texto_base

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        is_auth = bool(tracker.get_slot("is_authenticated") or _has_auth(tracker))
        if not is_auth:
            dispatcher.utter_message(response="utter_login_requerido")
            return []

        certificados = self._obtener_certificados_backend(tracker)
        if certificados is None or len(certificados) == 0:
            certificados = self._certificados_demo()

        certificados_md = self._formatear_certificados_md(certificados)

        try:
            texto_base = self._build_resumen_tecnico(certificados)
            contexto_llm = {
                "flujo": "consultar_certificados_menu",
                "cantidad_certificados": len(certificados),
            }
            resumen_llm = llm_summarize_with_ollama(texto_base, contexto_llm)

            if resumen_llm and resumen_llm.strip():
                dispatcher.utter_message(text=resumen_llm.strip())
        except Exception:
            
            pass

        dispatcher.utter_message(
            response="utter_certificado_listado",
            certificados_md=certificados_md,
        )

        return []
