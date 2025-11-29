# rasa/actions/acciones_certificados.py
from __future__ import annotations
from typing import Any, Dict, List, Text

import os
import logging
import requests

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType

from .common import _is_auth, _has_auth, _auth_headers
from .acciones_llm import llm_summarize_with_ollama

logger = logging.getLogger(__name__)


def build_certificados_summary(certificados: List[Dict[str, Any]]) -> str:
    """
    Construye un resumen textual 'técnico' a partir de la lista de certificados.
    Ajusta las claves según el JSON real de tu backend.

    Esperado algo como:
    [
      {
        "tipo": "estudio",
        "programa": "Gestión administrativa",
        "fecha_emision": "2024-05-10"
      },
      ...
    ]
    """
    if not certificados:
        return (
            "Por ahora no aparecen certificados registrados en tu cuenta. "
            "Si consideras que debería haber alguno, puedes verificar en la plataforma Zajuna "
            "o contactar a soporte."
        )

    total = len(certificados)
    por_tipo: Dict[str, int] = {}
    ejemplos: List[str] = []

    for c in certificados:
        tipo = str(c.get("tipo", "otro")).lower()
        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

        programa = c.get("programa") or c.get("nombre") or "Programa no especificado"
        fecha = c.get("fecha_emision") or c.get("fecha") or "fecha no disponible"
        ejemplos.append(f"- {programa} (tipo: {tipo}, fecha: {fecha})")

    resumen_tipos = ", ".join(f"{n} de {t}" for t, n in por_tipo.items())

    texto = (
        f"Tienes {total} certificado(s) disponibles en tu cuenta. "
        f"Distribución por tipo: {resumen_tipos}.\n\n"
        "Algunos ejemplos:\n"
        + "\n".join(ejemplos[:5])
    )
    return texto


def _get_certificados_desde_slot_o_mock(tracker: Tracker) -> List[Dict[str, str]]:
    """
    Intenta leer una lista de certificados desde el slot 'certificados'.

    Estructura esperada (lista de dicts):
    [
      {
        "titulo": "Introducción a Programación",
        "fecha": "2024-06-10",
        "ver_url": "https://...",
        "descargar_url": "https://...",
        "img": "https://..."
      },
      ...
    ]

    Si el slot existe y es una lista:
      - si está vacío => interpretamos como "sin certificados".
      - si tiene elementos => los normalizamos.

    Si no existe slot => retornamos un mock de ejemplo (para demo).

    Esto permite usar un fallback (utter_certificados_carousel) cuando el slot
    se establece explícitamente como [] desde el backend o alguna acción previa.
    """
    data = tracker.get_slot("certificados")

    if isinstance(data, list):
        # Slot presente: lista de certificados
        if not data:
            # Lista vacía => sin certificados reales
            return []

        norm: List[Dict[str, str]] = []
        for c in data:
            norm.append(
                {
                    "titulo": c.get("titulo") or c.get("title") or "Certificado",
                    "fecha": c.get("fecha") or c.get("date") or "s/f",
                    "ver_url": c.get("ver_url") or c.get("view_url") or "#",
                    "descargar_url": c.get("descargar_url") or c.get("download_url") or "#",
                    "img": c.get("img") or c.get("image_url") or "",
                }
            )
        return norm

    # Modo demo / fallback: ejemplos por defecto
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
    elements: List[Dict[str, Any]] = []
    for c in certificados:
        buttons = [
            {"type": "web_url", "url": c["ver_url"], "title": "Ver PDF"},
            {"type": "web_url", "url": c["descargar_url"], "title": "Descargar"},
        ]
        el: Dict[str, Any] = {
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


class ActionRenderCertificados(Action):
    """Renderiza certificados a partir del slot 'certificados':

    - Si hay datos en el slot, los normaliza y:
        * Para Facebook: envía un carrusel (generic template).
        * Para otros canales: envía una lista Markdown con botones.

    - Si el slot está vacío:
        * Usa 'utter_certificados_carousel' como fallback.

    - Requiere autenticación (_is_auth o _has_auth) para evitar mostrar datos sensibles
      a usuarios no autenticados.
    """

    def name(self) -> Text:
        return "action_render_certificados"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        # Seguridad: solo usuarios autenticados ven certificados reales
        if not (_is_auth(tracker) or _has_auth(tracker)):
            dispatcher.utter_message(response="utter_login_hint")
            return []

        certificados = _get_certificados_desde_slot_o_mock(tracker)

        # Si no hay certificados ni siquiera en slot → fallback
        if not certificados:
            dispatcher.utter_message(response="utter_certificados_carousel")
            return []

        canal = (tracker.get_latest_input_channel() or "").lower()

        # Facebook → carrusel nativo
        if "facebook" in canal:
            payload = _render_facebook_generic_template(certificados)
            dispatcher.utter_message(json_message=payload)
            return []

        # Otros canales → lista Markdown + botones
        texto = _render_markdown_certificados(certificados)
        dispatcher.utter_message(
            text=texto,
            buttons=[
                {"title": "🏠 Menú principal", "payload": "/ir_menu_principal"},
                {"title": "❌ Terminar", "payload": "/terminar_conversacion"},
            ],
        )
        return []


class ActionMostrarCertificadosCarousel(Action):
    def name(self) -> Text:
        return "action_mostrar_certificados_carousel"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        # 1) Si NO está autenticado → explicación modo invitado usando LLM
        if not _is_auth(tracker):
            base_url = tracker.get_slot("zajuna_base_url") or "https://zajuna.edu"
            texto_base = (
                "Para mostrarte un carrusel con tus certificados reales, necesito que inicies sesión en Zajuna.\n\n"
                "1) Abre el portal de Zajuna.\n"
                "2) Inicia sesión con tu cuenta.\n"
                "3) Vuelve aquí y escribe: \"ver certificados\".\n\n"
                f"También puedes ir directamente a: {base_url}/login"
            )
            contexto = {"flujo": "certificados_modo_invitado"}
            mensaje = llm_summarize_with_ollama(texto_base, contexto)
            dispatcher.utter_message(text=mensaje)
            return []

        # 2) Usuario autenticado → obtenemos certificados del backend
        certificados: List[Dict[str, Any]] = []

        try:
            base_url = os.getenv("BACKEND_BASE_URL", "")
            if base_url:
                resp = requests.get(
                    f"{base_url}/api/certificados",
                    headers=_auth_headers(tracker),
                    timeout=10,
                )
                if resp.ok:
                    data = resp.json() or {}
                    certificados = data.get("certificados", [])
        except Exception:
            logger.exception("Error al consultar certificados para el carrusel.")

        # 3) Mensaje resumen textual con LLM (a partir de datos reales)
        texto_base = build_certificados_summary(certificados)
        contexto_llm = {
            "flujo": "certificados_carousel",
            "cantidad_certificados": len(certificados),
        }
        mensaje = llm_summarize_with_ollama(texto_base, contexto_llm)
        dispatcher.utter_message(text=mensaje)

        # 4) Carrusel: mantenemos lógica de negocio (placeholder genérico,
        #    puedes adaptarlo al formato de tu canal si ya tienes uno)
        elements: List[Dict[str, Any]] = []
        for c in certificados[:10]:
            titulo = c.get("programa") or c.get("nombre") or "Certificado"
            tipo = c.get("tipo", "certificado")
            fecha = c.get("fecha_emision") or c.get("fecha") or ""
            elements.append(
                {
                    "title": titulo,
                    "subtitle": f"Tipo: {tipo} | Fecha: {fecha}",
                    "buttons": [
                        {
                            "title": "Ver/descargar",
                            "payload": "/descargar_certificado",
                        }
                    ],
                }
            )

        if elements:
            dispatcher.utter_message(
                attachment={"type": "template", "payload": {"elements": elements}}
            )
        else:
            dispatcher.utter_message(
                text="No encontré certificados para mostrar en el carrusel en este momento."
            )

        return []
