# rasa/actions/acciones_certificados.py
from __future__ import annotations
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType


def _get_certificados_desde_slot_o_mock(tracker: Tracker) -> List[Dict[str, str]]:
    """
    Intenta leer una lista de certificados desde el slot 'certificados'.
    Estructura esperada (lista de dicts):
    [
      {"titulo": "Introducción a Programación", "fecha": "2024-06-10",
       "ver_url": "https://...", "descargar_url": "https://...", "img": "https://..."},
      ...
    ]
    Si no existe, retorna un mock de ejemplo.
    """
    data = tracker.get_slot("certificados")
    if isinstance(data, list) and data:
        # normaliza claves por si vienen distintas
        norm = []
        for c in data:
            norm.append({
                "titulo": c.get("titulo") or c.get("title") or "Certificado",
                "fecha": c.get("fecha") or c.get("date") or "s/f",
                "ver_url": c.get("ver_url") or c.get("view_url") or "#",
                "descargar_url": c.get("descargar_url") or c.get("download_url") or "#",
                "img": c.get("img") or c.get("image_url") or "",
            })
        return norm

    # Mock por defecto (seguro para demo)
    return [
        {
            "titulo": "Introducción a Programación",
            "fecha": "2024-06-10",
            "ver_url": "https://zajuna.sena.edu.co/cert/123",
            "descargar_url": "https://zajuna.sena.edu.co/cert/123/download",
            "img": "https://tu-cdn/certificados/programacion.png",
        },
        {
            "titulo": "Bases de Datos",
            "fecha": "2025-03-15",
            "ver_url": "https://zajuna.sena.edu.co/cert/456",
            "descargar_url": "https://zajuna.sena.edu.co/cert/456/download",
            "img": "https://tu-cdn/certificados/bd.png",
        },
    ]


def _render_markdown_certificados(certificados: List[Dict[str, str]]) -> str:
    """Render de lista rica Markdown para canales no-Facebook."""
    lineas = ["📜 **Tus certificados disponibles**"]
    for i, c in enumerate(certificados, start=1):
        lineas.append(
            f"""{i}) *{c['titulo']}* — {c['fecha']}  
   • [Ver PDF]({c['ver_url']})  
   • [Descargar]({c['descargar_url']})"""
        )
    return "\n\n".join(lineas)


def _render_facebook_generic_template(certificados: List[Dict[str, str]]) -> Dict[str, Any]:
    """Payload de 'generic template' para Messenger (carrusel nativo)."""
    elements = []
    for c in certificados:
        buttons = [
            {"type": "web_url", "url": c["ver_url"], "title": "Ver PDF"},
            {"type": "web_url", "url": c["descargar_url"], "title": "Descargar"},
        ]
        el = {
            "title": c["titulo"][:80],
            "subtitle": f"Emitido: {c['fecha']}",
            "buttons": buttons,
        }
        if c.get("img"):
            el["image_url"] = c["img"]
        elements.append(el)

    return {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": elements[:10],  # máx 10 por carrusel
            },
        }
    }


class ActionConsultarCertificados(Action):
    """Muestra certificados con carrusel Facebook o Markdown con botones en otros canales."""

    def name(self) -> Text:
        return "action_consultar_certificados"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[EventType]:

        # 1) Puerta de autenticación (usa tu slot global)
        if not bool(tracker.get_slot("is_authenticated")):
            # Usa tu hint de login si la tienes, o un prompt corto.
            dispatcher.utter_message(response="utter_login_hint")
            return []

        # 2) Carga certificados dinámicos o mock
        certificados = _get_certificados_desde_slot_o_mock(tracker)

        # 3) Detección de canal
        canal = tracker.get_latest_input_channel() or ""
        canal = canal.lower()

        if "facebook" in canal:
            # Carrusel nativo Messenger
            payload = _render_facebook_generic_template(certificados)
            dispatcher.utter_message(json_message=payload)
            return []

        # 4) Fallback para otros canales: Markdown + botones
        texto = _render_markdown_certificados(certificados)
        dispatcher.utter_message(
            text=texto,
            buttons=[
                {"title": "🏠 Menú principal", "payload": "/ir_menu_principal"},
                {"title": "❌ Terminar", "payload": "/terminar_conversacion"},
            ],
        )
        return []
