# ruta: rasa/actions/acciones_enviar_soporte.py
from __future__ import annotations
from typing import Any, Dict, List, Text
import os
import json
import datetime

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType

from .acciones_llm import llm_summarize_with_ollama

_STORE_DIR = "data"
_TICKETS_FILE = os.path.join(_STORE_DIR, "soporte.jsonl")


def _append_ticket(record: Dict[str, Any]) -> bool:
    try:
        os.makedirs(_STORE_DIR, exist_ok=True)
        with open(_TICKETS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


class ActionEnviarSoporteDirecto(Action):
    def name(self) -> Text:
        return "action_enviar_soporte_directo"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        nombre = (tracker.get_slot("nombre") or "").strip() or "Usuario"
        email = (tracker.get_slot("email") or "").strip() or "sin-correo@ejemplo.com"
        motivo = (tracker.get_slot("motivo_soporte") or "").strip() or "otro"
        mensaje = (
            (tracker.latest_message.get("text") or "").strip()
            or "Solicitud de soporte directo (sin detalle)."
        )
        prefer = (tracker.get_slot("prefer_contacto") or "").strip() or "email"
        phone = (tracker.get_slot("phone") or "").strip()

        payload = {
            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sender_id": tracker.sender_id,
            "nombre": nombre,
            "email": email,
            "motivo": motivo,
            "mensaje": mensaje,
            "prefer_contacto": prefer,
            "phone": phone,
            "ultimo_intent": (tracker.latest_message.get("intent") or {}).get("name"),
            "tipo": "soporte_directo",
        }

        ok = _append_ticket(payload)

        if ok:
            # 🧾 Texto base técnico (sin inventar nada)
            resumen_mensaje = mensaje.strip()
            if len(resumen_mensaje) > 400:
                resumen_mensaje = resumen_mensaje[:400].rstrip() + "…"

            texto_base = (
                "Se registró una solicitud de soporte directo para el equipo de ayuda. "
                "Incluye los siguientes datos:\n"
                f"- Nombre reportado: {nombre}\n"
                f"- Motivo principal: {motivo}\n"
                f"- Preferencia de contacto: {prefer}\n"
                f"- Teléfono (si lo dio): {phone or 'no registrado'}\n"
                f"- Descripción del problema: {resumen_mensaje}\n\n"
                "Agradece al usuario por confiar en el soporte y explícale que un agente "
                "revisará su caso y se pondrá en contacto por el medio indicado."
            )

            contexto_llm = {
                "flujo": "soporte_directo",
                "motivo_soporte": motivo,
                "prefer_contacto": prefer,
                "tiene_phone": bool(phone),
            }

            # ✨ Usamos el LLM solo para mejorar redacción y tono
            try:
                mensaje_final = llm_summarize_with_ollama(texto_base, contexto_llm)
                dispatcher.utter_message(text=mensaje_final)
            except Exception:
                # Fallback si el LLM falla
                dispatcher.utter_message(
                    text=(
                        "✅ He enviado tu solicitud de soporte directo. "
                        "Un agente te contactará en breve."
                    )
                )
        else:
            # ❌ Error técnico → mensaje directo, sin LLM
            dispatcher.utter_message(
                text=(
                    "⚠️ No pude registrar el soporte directo ahora mismo. "
                    "Por favor, inténtalo de nuevo más tarde o pide hablar con un asesor humano."
                )
            )

        return []
