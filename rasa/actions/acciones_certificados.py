# ruta: rasa/actions/acciones_certificados.py
from __future__ import annotations

from typing import Any, Dict, List, Text, Optional
import logging

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType

from .core.llm_engine import run_llm
from .acciones.zajuna_flow_helpers import require_auth, safe_backend_get

logger = logging.getLogger(__name__)


# ================================================================
# 📦 DOMAIN LOGIC (PURO)
# ================================================================

def build_certificados_summary(certificados: List[Dict[str, Any]]) -> str:

    if not certificados:
        return "No tienes certificados registrados en este momento."

    total = len(certificados)
    por_tipo: Dict[str, int] = {}
    ejemplos: List[str] = []

    for c in certificados:
        tipo = str(c.get("tipo", "otro")).lower()
        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

        programa = c.get("programa") or c.get("nombre") or "N/D"
        fecha = c.get("fecha_emision") or c.get("fecha") or "N/D"

        ejemplos.append(f"- {programa} ({tipo}, {fecha})")

    resumen_tipos = ", ".join(f"{n} de {t}" for t, n in por_tipo.items())

    return (
        f"Tienes {total} certificado(s).\n"
        f"Distribución: {resumen_tipos}.\n\n"
        "Ejemplos:\n" + "\n".join(ejemplos[:5])
    )


# ================================================================
# 📜 MAIN ACTION (PRODUCCIÓN ESTABLE)
# ================================================================

class ActionRenderCertificados(Action):

    def name(self) -> Text:
        return "action_render_certificados"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        # --------------------------------------------------------
        # AUTH LAYER
        # --------------------------------------------------------
        if require_auth(dispatcher, tracker, "certificados", "academico"):
            return []

        # --------------------------------------------------------
        # FAST PATH
        # --------------------------------------------------------
        certificados = tracker.get_slot("certificados") or []

        if not isinstance(certificados, list):
            certificados = []

        # --------------------------------------------------------
        # BACKEND SAFE CALL (CORREGIDO: Unificación de respuesta vs response)
        # --------------------------------------------------------
        respuesta = safe_backend_get(tracker, "/api/certificados", default={})

        if not isinstance(respuesta, dict):
            respuesta = {}

        if not certificados:
            certificados = respuesta.get("certificados") or []

        # --------------------------------------------------------
        # EMPTY STATE
        # --------------------------------------------------------
        if not certificados:
            dispatcher.utter_message(response="utter_certificados_carousel")
            return []

        # --------------------------------------------------------
        # LLM SAFE LAYER
        # --------------------------------------------------------
        summary = build_certificados_summary(certificados)

        llm_text = run_llm(
            prompt=summary,
            tracker=tracker,
            fallback=summary,
        )

        final_text = llm_text if isinstance(llm_text, str) and llm_text.strip() else summary

        dispatcher.utter_message(text=final_text)

        # --------------------------------------------------------
        # CHANNEL ROUTING (CORREGIDO: Extracción segura del canal)
        # --------------------------------------------------------
        # Rasa almacena el canal directamente en una propiedad de lectura del tracker
        channel = ""
        try:
            channel = str(tracker.get_latest_input_channel() or "").lower()
        except Exception:
            # Fallback seguro en caso de llamadas internas de testing/CLI de Rasa
            channel = "default"

        if "facebook" in channel:

            elements = [
                {
                    "title": c.get("titulo") or c.get("nombre") or "Certificado",
                    "subtitle": c.get("fecha") or "",
                    "buttons": [
                        {"type": "web_url", "url": c.get("ver_url", "#"), "title": "Ver"},
                        {"type": "web_url", "url": c.get("descargar_url", "#"), "title": "Descargar"},
                    ],
                }
                for c in certificados[:10]
            ]

            dispatcher.utter_message(
                json_message={
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "generic",
                            "elements": elements
                        }
                    }
                }
            )

            return []

        # --------------------------------------------------------
        # DEFAULT OUTPUT
        # --------------------------------------------------------
        lines = ["📜 Certificados disponibles:"]

        for c in certificados[:5]:
            lines.append(f"- {c.get('titulo') or c.get('nombre')}")

        dispatcher.utter_message(text="\n".join(lines))

        return []