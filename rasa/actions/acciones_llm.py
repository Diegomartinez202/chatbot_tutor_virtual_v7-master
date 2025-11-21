# ==========================================================
# actions/actions_llm.py  (VERSIÓN OPTIMIZADA + ROBUSTA)
# ==========================================================

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
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "350"))
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "15"))


# ==========================================================
# 🔥 PROMPT PROFESIONAL PARA UN TUTOR DEL SENA + LLM HÍBRIDO
# ==========================================================
PROMPT_SYSTEM = """
Eres *Tutor Virtual Profesional del SENA*, especializado en formación por competencias.
TU MISIÓN:
- Explicar temas académicos de manera clara, didáctica y estructurada.
- Ser amable, profesional y preciso.
- Ajustarte al contexto educativo colombiano.

REGLAS OBLIGATORIAS:
1. Nunca inventes datos institucionales. Si no sabes, responde:
   "No tengo la información exacta; puedo orientarte en el proceso general."
2. No uses lenguaje técnico excesivo; prioriza comprensión del aprendiz.
3. Si el usuario pregunta sobre certificados, estados académicos o procesos reales:
   → NO des datos personales.
   → Explica el procedimiento oficial.
4. Tú solo puedes responder en uno de estos dos formatos:
   - INTENT:<nombre_intent>
   - RESPUESTA:<texto pedagógico>

ESTRUCTURA DE RESPUESTA (cuando uses RESPUESTA):
1) Definición breve
2) Pasos claros
3) Ejemplo práctico
4) Recomendación final (siguiente paso sugerido)

Cumple SIEMPRE esta estructura.
"""


# ==========================================================
# 🔒 ANONIMIZACIÓN ROBUSTA
# ==========================================================
def anonymize_text(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]", text)
    text = re.sub(r"\b\d{6,}\b", "[NUM]", text)
    text = re.sub(r"\b(?:\d[ -]*?){13,19}\b", "[NUM]", text)
    text = re.sub(
        r"\b[A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s[A-ZÁÉÍÓÚ][a-záéíóú]+){0,2}\b",
        "[NAME]", text)
    text = re.sub(
        r"\b(?:calle|cra|carrera|av|avenida|cll)\b[^\n,]{0,40}",
        "[ADDRESS]", text, flags=re.IGNORECASE)
    return text


# ==========================================================
# ⚡ LLAMADA A OLLAMA (MEJORADA)
# ==========================================================
def call_ollama(prompt: str) -> str:
    url = f"{OLLAMA_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "max_tokens": OLLAMA_MAX_TOKENS,
        "temperature": 0.15,
        "top_p": 0.9,
        "repeat_penalty": 1.05,
    }

    try:
        resp = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        # Diferentes versiones de Ollama → manejar todos los formatos
        if isinstance(data, dict):
            for key in ["response", "generated", "result"]:
                if key in data and isinstance(data[key], str):
                    return data[key].strip()

            if "results" in data and isinstance(data["results"], list):
                r0 = data["results"][0]
                for key in ["content", "text", "output"]:
                    if key in r0:
                        return str(r0[key]).strip()

        if isinstance(data, str):
            return data.strip()

        return ""

    except Exception as e:
        logger.exception("❌ Error llamando a Ollama")
        return ""


# ==========================================================
# 🧠 PARSER DE RESPUESTA INTELIGENTE
# ==========================================================
def parse_llm_response(text: str) -> Dict[str, str]:
    if not text:
        return {"type": "raw", "value": ""}

    t = text.strip()

    # Buscar INTENT aunque venga rodeado de texto adicional
    m_int = re.search(r"INTENT\s*:\s*([a-zA-Z0-9_]+)", t, flags=re.I)
    if m_int:
        return {"type": "intent", "value": m_int.group(1).strip()}

    # Buscar RESPUESTA: aunque venga con saltos o espacios
    m_resp = re.search(r"RESPUESTA\s*:\s*(.+)", t, flags=re.I | re.S)
    if m_resp:
        return {"type": "response", "value": m_resp.group(1).strip()}

    # Intentar JSON
    try:
        j = json.loads(t)
        if "intent" in j:
            return {"type": "intent", "value": j["intent"]}
        if "response" in j:
            return {"type": "response", "value": j["response"]}
    except:
        pass

    return {"type": "raw", "value": t}


# ==========================================================
# 🎯 ACCIÓN PRINCIPAL: ActionHandleWithOllama
# ==========================================================
class ActionHandleWithOllama(Action):
    def name(self) -> Text:
        return "action_handle_with_llm"

    # ---- Construcción del prompt con historial reducido ----
    def build_prompt(self, tracker: Tracker) -> str:
        user_msg = anonymize_text(tracker.latest_message.get("text", ""))
        intent_info = tracker.latest_message.get("intent", {})

        # historial corto (máx 6 turnos)
        history = []
        for e in tracker.events[-12:]:
            if e.get("event") == "user":
                history.append("Usuario: " + anonymize_text(e.get("text", "")))
            elif e.get("event") == "bot":
                history.append("Bot: " + str(e.get("text", "")))

        hist_text = "\n".join(history[-6:])

        prompt = (
            PROMPT_SYSTEM
            + "\n\n=== CONTEXTO DE LA CONVERSACIÓN ===\n"
            + f"Último mensaje del usuario: {user_msg}\n"
            + f"Intent detectado por Rasa: {intent_info.get('name')} "
            + f"(conf={intent_info.get('confidence')})\n"
            + f"Historial breve:\n{hist_text}\n"
            + "\nResponde ÚNICAMENTE en formato:\n"
            + "INTENT:<nombre_intent>  o  RESPUESTA:<texto>\n"
        )
        return prompt

    # ---- Ejecución principal ----
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        prompt = self.build_prompt(tracker)
        logger.info(f"[LLM PROMPT] {prompt[:400]}...")

        raw = call_ollama(prompt)

        if not raw:
            dispatcher.utter_message(
                text="No puedo procesar tu solicitud en este momento. ¿Podrías reformularla?"
            )
            return []

        parsed = parse_llm_response(raw)
        logger.info(f"[LLM PARSED] {parsed}")

        # --- Si Ollama sugiere INTENT ---
        if parsed["type"] == "intent":
            dispatcher.utter_message(
                text=f"Entendido, procederé con tu solicitud."
            )
            return [
                SlotSet("llm_suggested_intent", parsed["value"]),
                SlotSet("from_llm", True)
            ]

        # --- Si es texto normal ---
        if parsed["type"] == "response":
            dispatcher.utter_message(text=parsed["value"])
            return [SlotSet("from_llm", True)]

        # --- Raw fallback ---
        dispatcher.utter_message(text=parsed["value"])
        return [SlotSet("from_llm", True)]
