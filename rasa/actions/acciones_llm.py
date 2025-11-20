# actions/actions_llm.py
import os
import re
import logging
import requests
import json
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ----------------- CONFIG DESDE ENV -----------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434") 
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")          
OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "250"))
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "12"))

# ----------------- PROMPT DEL SENA -----------------
PROMPT_SYSTEM = """
Eres un Tutor Académico del SENA (Centro de Formación Profesional).

RESPONSABILIDADES:
- Proveer explicaciones pedagógicas, claras y concisas, en español neutro.
- Ofrecer definiciones, procesos, ejemplos prácticos, pasos y referencias institucionales cuando existan.
- No inventar normativa ni procedimientos; si no estás seguro, usa:
  "No tengo la información exacta; puedo orientarte sobre el proceso general."
- Si la solicitud requiere acceso a datos personales o sistemas (SofíaPlus, certificados),
  indica el procedimiento y enlaces oficiales, sin requerir credenciales.

FORMATO DE RESPUESTA (OBLIGATORIO):
- Si la respuesta debe activar una acción (inscripción, descarga, ver certificado), devuelve exactamente:
    INTENT:<nombre_intent>
  Ej.: INTENT:solicitar_inscripcion

- Si la respuesta es texto para el usuario, devuelve exactamente:
    RESPUESTA:<texto ciudadano>
  Ej.: RESPUESTA:Para inscribirte en SofíaPlus, ingresa a https://oferta.senasofiaplus.edu.co y sigue los pasos...

SEGUIDOR DIDÁCTICO (estructura recomendada en RESPUESTA):
1) Definición breve (1–2 frases).
2) Procesos / pasos (lista corta).
3) Ejemplo práctico (1 caso pequeño aplicado al SENA).
4) Recursos / enlaces oficiales (si aplica).
5) Sugerencia de siguiente tema o pregunta.

EJEMPLOS:
Usuario: "Explícame Administración de Recursos Humanos"
→ RESPUESTA:Administración de Recursos Humanos: [definición]. Pasos: 1)... Ejemplo: ... Recursos: https://oferta.senasofiaplus.edu.co

Usuario: "Quiero mi certificado"
→ INTENT:solicitar_certificado

SEGURIDAD Y PRIVACIDAD:
- ANONIMIZA cualquier dato personal (reemplaza números o correos por [NUM] / [EMAIL]).
- No proporciones números de expediente ni enlaces privados.
"""

# ----------------- ANONIMIZACIÓN -----------------
def anonymize_text(text: str) -> str:
    if not text:
        return text
    # correos
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]", text)
    # números de documento / teléfonos (secuencias de 6 o más dígitos)
    text = re.sub(r"\b\d{6,}\b", "[NUM]", text)
    # tarjetas, secuencias con guiones
    text = re.sub(r"\b(?:\d[ -]*?){13,19}\b", "[NUM]", text)
    # nombres simples: mayúscula seguido de minúsculas (ojo: puede tener falsos positivos)
    text = re.sub(
        r"\b[A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s[A-ZÁÉÍÓÚ][a-záéíóú]+){0,2}\b",
        "[NAME]",
    )
    # direcciones (número + calle)
    text = re.sub(
        r"\b(?:calle|cra|carrera|av|avenida|cll)\b[^\n,]{0,40}",
        "[ADDRESS]",
        text,
        flags=re.IGNORECASE,
    )
    return text

# ----------------- LLAMADA A OLLAMA -----------------
def call_ollama(prompt: str) -> str:
    url = f"{OLLAMA_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "max_tokens": OLLAMA_MAX_TOKENS,
        "temperature": 0.2,
        "top_p": 0.95,
        "repeat_penalty": 1.0,
    }
    try:
        resp = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        # parsing robusto: diferentes versiones de Ollama pueden devolver campos distintos
        if isinstance(data, dict):
            # ejemplo: {"generated": "..."} o {"response": "..."} o {"results":[{"content":"..."}]}
            if "response" in data and isinstance(data["response"], str):
                return data["response"].strip()
            if "generated" in data and isinstance(data["generated"], str):
                return data["generated"].strip()
            if "result" in data and isinstance(data["result"], str):
                return data["result"].strip()
            if "results" in data and isinstance(data["results"], list) and data["results"]:
                r0 = data["results"][0]
                if isinstance(r0, dict):
                    for key in ("content", "text", "output"):
                        if key in r0 and isinstance(r0[key], str):
                            return r0[key].strip()
        # fallback: si viene texto plano
        if isinstance(data, str):
            return data.strip()
        return ""
    except Exception as e:
        logger.exception("Error llamando a Ollama: %s", e)
        return ""

# ----------------- PARSER RESPUESTA LLM -----------------
def parse_llm_response(text: str) -> Dict[str, str]:
    if not text:
        return {"type": "raw", "value": ""}
    t = text.strip()
    if t.upper().startswith("INTENT:"):
        return {"type": "intent", "value": t.split(":", 1)[1].strip()}
    if t.upper().startswith("RESPUESTA:"):
        return {"type": "response", "value": t.split(":", 1)[1].strip()}
    # intentar JSON
    try:
        j = json.loads(t)
        if isinstance(j, dict):
            if "intent" in j:
                return {"type": "intent", "value": j.get("intent")}
            if "response" in j:
                return {"type": "response", "value": j.get("response")}
    except Exception:
        pass
    return {"type": "raw", "value": t}

# ----------------- ACTION -----------------
class ActionHandleWithOllama(Action):
    def name(self) -> Text:
        return "action_handle_with_llm"

    def build_prompt(self, tracker: Tracker) -> str:
        last_user = tracker.latest_message.get("text", "") or ""
        last_user_anon = anonymize_text(last_user)

        intent = tracker.latest_message.get("intent", {}) or {}
        intent_name = intent.get("name", "unknown")
        intent_conf = intent.get("confidence", 0.0)

        # historial breve
        last_events: List[str] = []
        for e in tracker.events[-12:]:
            if e.get("event") == "user":
                txt = e.get("text", "")
                last_events.append("Usuario: " + anonymize_text(txt))
            elif e.get("event") == "bot":
                txt = e.get("text", "")
                if isinstance(txt, list):
                    txt = ". ".join(
                        [
                            (t.get("text") if isinstance(t, dict) else str(t))
                            for t in txt
                        ]
                    )
                last_events.append("Bot: " + (txt or ""))

        hist_text = "\n".join(last_events[-8:])

        prompt = (
            PROMPT_SYSTEM
            + "\n\nContexto (no inventes datos sensibles):\n"
            + f"Último mensaje (anonimizado): {last_user_anon}\n"
            + f"Intent detectado por Rasa: {intent_name} (conf={intent_conf})\n"
            + f"Historial breve:\n{hist_text}\n\n"
            + "Instrucciones: responde SOLO en el formato:\n"
            + "INTENT:<nombre_intent>  o  RESPUESTA:<texto>.\n"
            + "Si no estás seguro, devuelve RESPUESTA: con la orientación más útil posible.\n"
        )
        return prompt

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        prompt = self.build_prompt(tracker)
        dispatcher.utter_message(text="Procesando tu consulta...")  # opcional UX

        raw = call_ollama(prompt)
        if not raw:
            dispatcher.utter_message(
                text="No puedo procesar tu solicitud en este momento. Intenta de nuevo."
            )
            return []

        parsed = parse_llm_response(raw)

        if parsed["type"] == "intent":
            dispatcher.utter_message(text=f"Entendido. Procedo con: {parsed['value']}")
            return [SlotSet("llm_suggested_intent", parsed["value"])]

        elif parsed["type"] == "response":
            dispatcher.utter_message(text=parsed["value"])
            return []

        else:
            dispatcher.utter_message(
                text=parsed["value"]
                or "Lo siento, no pude generar una respuesta segura."
            )
            return []
