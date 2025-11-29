# ==========================================================
# actions/actions_llm.py  (VERSIÓN OPTIMIZADA + ROBUSTA)
# ==========================================================

import os
import re
import logging
import requests
import json
import unicodedata
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
from .actions_semantic_memory import store_message, retrieve_similar

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ----------------- CONFIG DESDE ENV -----------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "350"))
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "60"))


# ==========================================================
# 🔥 PROMPT PROFESIONAL PARA UN TUTOR DEL SENA + LLM HÍBRIDO
# ==========================================================
PROMPT_SYSTEM = """
Eres el *Tutor Virtual Oficial del SENA*, diseñado para apoyar formación por competencias
y educación basada en resultados de aprendizaje.

🎓 ROLES:
- Tutor académico (explica temas con claridad).
- Instructor técnico (da procesos y procedimientos).
- Coach pedagógico (ayuda a comprender con ejemplos reales).
- Mentor emocional (detecta frustración y acompaña con empatía).

🎯 OBJETIVO GENERAL:
Brindar explicaciones en español claro, con estructura didáctica, sin inventar datos
institucionales, y adaptándote al nivel del aprendiz.

====================================================
📌 FORMATO DE RESPUESTA (OBLIGATORIO)
====================================================
Debes responder SOLO en uno de estos dos formatos:

1) **INTENT:<nombre_intent>**
   Ej.: INTENT:consultar_certificados

2) **RESPUESTA:<texto explicativo>**
   Donde <texto explicativo> DEBE seguir esta estructura:

1. Definición breve (máx 2 frases)
2. Pasos / procedimiento claro (viñetas)
3. Ejemplo práctico aplicado al SENA
4. Advertencias / errores comunes
5. Recomendación final o siguiente tema sugerido

====================================================
📌 NIVELES DE EXPLICACIÓN (Multi-Estilo)
====================================================
Adapta la complejidad según el usuario:

- *Nivel Básico:* usa analogías simples, ejemplos cotidianos.
- *Nivel Intermedio:* mezcla teoría + práctica.
- *Nivel Avanzado:* profundiza, usa términos técnicos, procesos detallados.

Identifica el nivel por el lenguaje del usuario.

====================================================
📌 REGLAS DE SEGURIDAD Y REALISMO
====================================================
- No inventes normas del SENA ni enlaces internos.
- Evita recomendaciones clínicas, médicas o legales.
- Si no sabes algo, responde con:
  "No tengo la información exacta; puedo orientarte sobre el procedimiento general."
- Anonimiza cualquier dato personal presente en los mensajes del usuario.

====================================================
📌 EJEMPLO DE FORMATO (correcto)
====================================================
Usuario: "Explícame contabilidad básica"

RESPUESTA:
Contabilidad básica: es el proceso de registrar y analizar las operaciones económicas.
Pasos:
- Identificar transacciones.
- Clasificar en cuentas.
- Registrar en libro diario.
Ejemplo:
Si una empresa compra materiales por $200.000, se registra como activo.
Errores comunes:
Mezclar gastos con compras.
Sugerencia:
Puedo enseñarte "partida doble" si quieres avanzar.

====================================================
FIN DEL PROMPT SISTEMA
====================================================
"""


# ==========================================================
# 🧩 NORMALIZACIÓN DE TEXTO (SIN TILDES, MINÚSCULAS)
# ==========================================================
def normalize(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower()


# ==========================================================
# 🧹 NORMALIZACIÓN "DE CHAT": ERRORES TÍPICOS, TILDES, ETC.
# ==========================================================
COMMON_CHAT_CORRECTIONS = {
    "kiero": "quiero",
    "kiere": "quiere",
    "kieres": "quieres",
    "xq": "porque",
    "xk": "porque",
    "xk?": "porque",
    "pa": "para",
    "q": "que",
    "qe": "que",
    "qer": "querer",
    "certifcado": "certificado",
    "certifcados": "certificados",
    "sertificado": "certificado",
    "sertificados": "certificados",
    "logaer": "lograr",
    "loguearme": "loguearme",
    "loguear": "loguear",
    "contraseña": "contrasena",   # para que coincida sin tilde
    "platafroma": "plataforma",
    "platafomra": "plataforma",
    "markeitng": "marketing",
    "markting": "marketing",
    "digitla": "digital",
}

def strip_accents(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
def normalize_chat_text(text: str) -> str:
    """
    Normaliza texto de usuario para que el bot entienda aunque escriba
    con errores:
    - tildes
    - letras repetidas
    - abreviaturas típicas de chat
    - SIN deformar palabras por reemplazos de caracteres sueltos
    """
    if not text:
        return ""

    # 1) Tu normalización base (minúsculas + quitar tildes, etc.)
    t = normalize(text)

    # 2) Colapsar letras repetidas: "holaaaa" -> "holaa" (o según tu criterio)
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)

    # 3) Tokenizar por palabras
    tokens = t.split()

    # 4) Correcciones específicas por palabra (evita el problema "k" → "queuiero")
    slang_map = {
        "k": "que",
        "xq": "porque",
        "xk": "porque",
        "kiero": "quiero",
        "aprnder": "aprender",
        # aquí puedes ir añadiendo más correcciones
    }

    # 5) Integramos también COMMON_CHAT_CORRECTIONS, pero por palabra
    #    (si utiliza las mismas claves, slang_map tiene prioridad)
    for wrong, right in COMMON_CHAT_CORRECTIONS.items():
        if wrong not in slang_map:
            slang_map[wrong] = right

    normalized_tokens = [slang_map.get(tok, tok) for tok in tokens]

    # 6) Reconstruir texto y limpiar espacios
    t = " ".join(normalized_tokens)
    t = re.sub(r"\s+", " ", t).strip()
    return t
# ==========================================================
# 🧩 CATEGORIZACIÓN DE MATERIAS (AMPLIADA)
# ==========================================================
# Nota: las llaves están en minúscula y sin tildes para facilitar el match.
MATERIAS: Dict[str, str] = {
    # --- Administración, RRHH, Finanzas, Contabilidad ---
    "administracion de recursos humanos": "Tutor en Administración de Recursos Humanos → Enfatiza gestión de personal, selección, capacitación y clima organizacional.",
    "gestion de recursos humanos": "Tutor en Gestión de Recursos Humanos → Procesos de talento humano, evaluación de desempeño y desarrollo organizacional.",
    "recursos humanos": "Tutor en Recursos Humanos → Procesos de selección, contratación y bienestar laboral.",
    "administracion financiera": "Tutor en Administración Financiera → Explica análisis financiero, presupuestos y toma de decisiones de inversión.",
    "administracion de empresas": "Tutor en Administración de Empresas → Enfocado en planeación, organización, dirección y control.",
    "finanzas y contabilidad": "Instructor de Finanzas y Contabilidad → Mezcla estados financieros, análisis y registros contables.",
    "contabilidad basica": "Instructor de Contabilidad → Ejercicios con registros básicos, asientos y partida doble.",
    "contabilidad": "Instructor de Contabilidad → Usa ejercicios con cifras y partida doble.",
    "costos y presupuestos": "Tutor de Costos y Presupuestos → Cálculo de costos, punto de equilibrio y presupuestación.",
    "servicio al cliente": "Tutor de Servicio al Cliente → Comunicación efectiva, manejo de quejas y experiencia del usuario.",
    "emprendimiento": "Mentor de Emprendimiento → Diseño de modelo de negocio, propuesta de valor y validación de ideas.",

    # --- Marketing, Comercio, Ventas ---
    "marketing digital": "Tutor de Marketing Digital → Estrategias en redes sociales, SEO, SEM y contenido.",
    "marketing": "Tutor de Marketing → Mezcla conceptos de mercado, mezcla de marketing y segmentación.",
    "comercio internacional": "Tutor de Comercio Internacional → Explica importaciones, exportaciones y logística internacional.",

    # --- Gestión de proyectos ---
    "gerencia de proyectos": "Tutor en Gerencia de Proyectos → Planificación, ejecución y control de proyectos.",
    "gestion de proyectos agiles": "Tutor en Gestión de Proyectos Ágiles → Scrum, Kanban y marcos adaptativos.",
    "gestion de proyectos": "Tutor en Gestión de Proyectos → Enfoque en alcance, tiempo y costos.",

    # --- Áreas administrativas y contables generales ---
    "ciencias administrativas y contables": "Tutor en Ciencias Administrativas y Contables → Integra conceptos de administración y contabilidad.",
    "ciencias administrativas": "Tutor en Ciencias Administrativas → Organización, dirección y control.",
    "ciencias contables": "Tutor en Ciencias Contables → Principios contables y registros financieros.",

    # --- Tecnología, desarrollo de software, TI ---
    "desarrollo de software": "Instructor de Desarrollo de Software → Lógica, programación, pruebas y buenas prácticas.",
    "desarrollo web": "Instructor de Desarrollo Web → HTML, CSS, JavaScript y frameworks.",
    "bases de datos": "Tutor de Bases de Datos → Modelo relacional, SQL y diseño de esquemas.",
    "ciberseguridad": "Tutor de Ciberseguridad → Buenas prácticas, amenazas comunes y controles básicos.",
    "inteligencia artificial": "Tutor de Inteligencia Artificial → Conceptos de modelos, entrenamiento y aplicaciones.",
    "analisis de datos": "Tutor de Análisis de Datos → Estadística básica, dashboards y toma de decisiones.",
    "big data": "Tutor de Big Data → Procesamiento de grandes volúmenes de datos y ecosistema analítico.",
    "machine learning": "Tutor de Machine Learning → Modelos supervisados, no supervisados y flujo de trabajo.",
    "desarrollo movil": "Instructor de Desarrollo Móvil → Aplicaciones para Android/iOS y patrones de diseño.",
    "cloud computing": "Tutor de Cloud Computing → Conceptos de IaaS, PaaS, SaaS y servicios en la nube.",
    "internet de las cosas": "Tutor de IoT → Dispositivos conectados, sensores y automatización.",
    "iot": "Tutor de IoT → Dispositivos conectados, sensores y automatización.",
    "realidad aumentada y virtual": "Tutor de RA/RV → Conceptos de entornos inmersivos y aplicaciones prácticas.",
    "realidad aumentada": "Tutor de Realidad Aumentada → Integración de elementos digitales en el mundo real.",
    "realidad virtual": "Tutor de Realidad Virtual → Experiencias inmersivas y simulaciones.",
    "blockchain": "Tutor de Blockchain → Explica bloques, cadenas, consensos y aplicaciones.",
    "robotica": "Tutor de Robótica → Sensores, actuadores, control y aplicaciones industriales.",
    "impresion 3d": "Tutor de Impresión 3D → Modelado básico y procesos de fabricación aditiva.",
    "automatizacion industrial": "Tutor de Automatización Industrial → PLC, sensores y sistemas de control.",
    "tecnologia": "Instructor Técnico → Procedimientos paso a paso con software y hardware.",
    "desarrollo de software": "Instructor de Desarrollo de Software → Lógica, programación, pruebas y buenas prácticas.",

    # --- Redes, telecomunicaciones, telemática ---
    "redes y telecomunicaciones": "Instructor de Redes y Telecomunicaciones → Topologías, protocolos y configuración básica.",
    "redes": "Instructor de Redes → Modelos OSI/TCP-IP, direccionamiento y configuración inicial.",
    "ciencias de la telematica y la comunicacion": "Tutor de Telemática y Comunicación → Integración de redes, servicios y transmisión de datos.",
    "telematica": "Tutor de Telemática → Redes avanzadas y servicios sobre IP.",
    "telecomunicaciones": "Tutor de Telecomunicaciones → Sistemas de transmisión y medios físicos.",

    # --- Diseño, UX/UI, creativas ---
    "diseno grafico": "Tutor de Diseño Gráfico → Principios visuales, tipografía y herramientas de diseño.",
    "ux/ui": "Tutor de UX/UI → Enfoque en experiencia de usuario e interfaces amigables.",
    "diseno ux/ui": "Tutor de UX/UI → Investigación, prototipado y pruebas de usabilidad.",
    "diseno ux": "Tutor de UX → Investigación con usuarios y arquitectura de información.",
    "diseno ui": "Tutor de UI → Composición visual, componentes e interacción.",

    # --- Logística, producción, mantenimiento, construcción ---
    "logistica": "Tutor de Logística → Gestión de inventarios, transporte y cadena de suministro.",
    "mantenimiento industrial": "Tutor de Mantenimiento Industrial → Tipos de mantenimiento y planificación.",
    "construccion": "Tutor de Construcción → Procesos constructivos, materiales y seguridad en obra.",
    "mantenimiento": "Tutor de Mantenimiento → Conceptos básicos de mantenimiento preventivo y correctivo.",

    # --- Seguridad, salud, ambiente, calidad ---
    "salud ocupacional": "Tutor de Salud Ocupacional → Riesgos laborales, prevención y normativa básica.",
    "seguridad industrial": "Tutor de Seguridad Industrial → Identificación de peligros y controles.",
    "gestion ambiental": "Tutor de Gestión Ambiental → Impacto ambiental, mitigación y normatividad básica.",
    "ciencias de la salud": "Tutor de Ciencias de la Salud → Conceptos generales de bienestar y cuidado.",
    "gestion de la calidad": "Tutor en Gestión de la Calidad → Enfoque en mejora continua y normas de calidad.",

    # --- Energía, electrónica, electricidad ---
    "energia renovable": "Tutor de Energías Renovables → Fuentes limpias, ventajas y aplicaciones.",
    "energias alternativas": "Tutor de Energías Alternativas → Opciones distintas a los combustibles fósiles.",
    "electronica": "Tutor de Electrónica → Circuitos básicos, componentes y mediciones.",
    "electricidad industrial": "Tutor de Electricidad Industrial → Instalaciones, motores y protección eléctrica.",

    # --- Mecánica, soldadura, automotriz, industrial ---
    "mecanica automotriz": "Tutor de Mecánica Automotriz → Sistemas del vehículo y diagnóstico básico.",
    "soldadura": "Tutor de Soldadura → Procesos, técnicas y seguridad.",
    "mecanica": "Tutor de Mecánica → Conceptos de fuerza, movimiento y sistemas mecánicos.",

    # --- Gastronomía, agricultura, turismo ---
    "gastronomia": "Tutor de Gastronomía → Técnicas culinarias, higiene y preparación de platos.",
    "agricultura": "Tutor de Agricultura → Cultivos, suelos y buenas prácticas agrícolas.",
    "turismo y hoteleria": "Tutor de Turismo y Hotelería → Servicio al cliente, operación hotelera y destinos.",
    "turismo": "Tutor de Turismo → Gestión de servicios turísticos y atención al visitante.",
    "hoteleria": "Tutor de Hotelería → Operación de alojamientos y atención al huésped.",

    # --- Ciencia básica, matemáticas, inglés ---
    "matematicas": "Tutor de Matemáticas → Razonamiento lógico, pasos claros y ejemplos numéricos.",
    "ciencias": "Tutor de Ciencias → Explica procesos naturales y experimentos simples.",
    "ingles": "Tutor de Inglés → Gramática básica, vocabulario y frases útiles.",

    # --- General / catch-all académico ---
    "tema academico": "Tutor Académico General → Explica conceptos teóricos con ejemplos sencillos.",
    "tema del sena": "Tutor General del SENA → Relaciona el tema con programas de formación.",
}


# ==========================================================
# 📝 PROMPT PARA RESUMIR / MEJORAR REDACCIÓN (NO INVENTAR DATOS)
# ==========================================================
SUMMARIZE_SYSTEM_PROMPT = """
Eres un asistente de redacción para el Tutor Virtual de Zajuna/SENA.

TU ÚNICA TAREA:
- Reescribir mensajes técnicos en un texto claro, amable y profesional.
- NO debes inventar ni cambiar datos de negocio (estado académico, notas, certificados, tickets, etc.).

REGLAS:
- Usa SIEMPRE español.
- Respeta todos los hechos: no cambies estados, fechas, cantidades, cursos, ni resultados.
- No inventes certificados, notas, accesos ni números de ticket.
- No des diagnósticos médicos, psicológicos ni legales.
- Si el texto base está claro, solo mejóralo ligeramente (tono más humano, mejor orden).

FORMATO DE SALIDA:
- Devuelve ÚNICAMENTE el texto final para el usuario.
- No incluyas etiquetas como 'INTENT:' ni 'RESPUESTA:'.
- No expliques qué estás haciendo, solo entrega el mensaje listo para mostrar.
"""


def detectar_materia(text: str) -> str:
    t = normalize_chat_text(text)
    for m, desc in MATERIAS.items():
        if m in t:
            return desc
    return "Tutor General del SENA"


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
        "[NAME]",
        text,
    )
    text = re.sub(
        r"\b(?:calle|cra|carrera|av|avenida|cll)\b[^\n,]{0,40}",
        "[ADDRESS]",
        text,
        flags=re.IGNORECASE,
    )
    return text

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

    except Exception:
        logger.exception("❌ Error llamando a Ollama")
        return ""

def llm_summarize_with_ollama(texto_base: str, contexto: Dict[str, Any]) -> str:
    """
    PERFIL:
    - Usa Ollama SOLO para mejorar redacción / estructura.
    - NO crea datos de negocio, NO decide autenticación, NO llama endpoints.
    """
    if not texto_base:
        return texto_base

    texto_anon = anonymize_text(texto_base)

    safe_pairs: List[str] = []
    for k, v in (contexto or {}).items():
        if v is None:
            continue
        k_str = str(k).lower()
        if any(
            s in k_str
            for s in ["token", "cedula", "documento", "password", "contrasena", "correo", "email"]
        ):
            continue
        safe_pairs.append(f"- {k}: {v}")

    contexto_str = "\n".join(safe_pairs) if safe_pairs else "Sin contexto adicional relevante."

    prompt = (
        SUMMARIZE_SYSTEM_PROMPT
        + "\n\n=== MENSAJE BASE (NO MODIFICAR HECHOS) ===\n"
        + texto_anon
        + "\n\n=== CONTEXTO NO SENSIBLE ===\n"
        + contexto_str
        + "\n\n=== INSTRUCCIONES ===\n"
        + "- Mejora el tono y la claridad del MENSAJE BASE.\n"
        + "- Mantén todos los datos, estados y resultados exactamente como están.\n"
        + "- No agregues información nueva.\n"
        + "- Devuelve solo el texto final para el usuario.\n"
    )

    raw = call_ollama(prompt)
    if not raw:
        return texto_base

    txt = raw.strip()
    txt = re.sub(r"^(RESPUESTA\s*:\s*)", "", txt, flags=re.IGNORECASE).strip()

    return txt or texto_base


def build_auth_required_message_for_action(nombre_proceso: str, base_url: str) -> str:
    """
    Construye un mensaje estándar de "esta acción requiere autenticación",
    con pasos claros para iniciar sesión en Zajuna, y lo pasa por el LLM
    solo para mejorar redacción.
    """
    texto_base = (
        f"Esta acción requiere que inicies sesión en la plataforma Zajuna para poder {nombre_proceso} "
        "y mostrarte datos reales asociados a tu usuario.\n\n"
        "Pasos para iniciar sesión en Zajuna:\n"
        f"1) Abre el portal: {base_url}/login\n"
        "2) Ingresa tu usuario o correo y tu contraseña.\n"
        "3) Si olvidaste tu contraseña, usa la opción \"¿Olvidé mi contraseña?\".\n"
        "4) Una vez dentro, vuelve a este chat y realiza de nuevo la misma consulta.\n\n"
        "Mientras tanto, puedo explicarte de forma general cómo funciona este proceso, "
        "pero no podré mostrarte aún tus datos personales."
    )

    contexto = {
        "flujo": "autenticacion_requerida",
        "proceso": nombre_proceso,
    }

    return llm_summarize_with_ollama(texto_base, contexto)


def parse_llm_response(text: str) -> Dict[str, str]:
    if not text:
        return {"type": "raw", "value": ""}

    t = text.strip()

    # Buscar INTENT aunque venga rodeado de texto adicional
    m_int = re.search(r"INTENT\s*:\s*([a-zA-Z0-9_]+)", t, flags=re.I)
    if m_int:
        return {"type": "intent", "value": m_int.group(1).strip()}

    # Buscar RESPUESTA:
    m_resp = re.search(r"RESPUESTA\s*:\s*(.+)", t, flags=re.I | re.S)
    if m_resp:
        value = m_resp.group(1).strip()
        value = re.split(r"\bINTENT\s*:", value, maxsplit=1)[0].strip()
        return {"type": "response", "value": value}

    # Intentar JSON
    try:
        j = json.loads(t)
        if isinstance(j, dict):
            if "intent" in j:
                return {"type": "intent", "value": str(j["intent"])}
            if "response" in j:
                return {"type": "response", "value": str(j["response"])}
    except Exception:
        pass

    return {"type": "raw", "value": t}


def _is_auth(tracker: Tracker) -> bool:
    """
    Helper simple para unificar la lógica de autenticación.
    """
    is_auth_slot = tracker.get_slot("is_authenticated")
    autenticado_slot = tracker.get_slot("autenticado")
    return bool(is_auth_slot or autenticado_slot)

class ActionHandleWithOllama(Action):
    def name(self) -> Text:
        return "action_handle_with_llm"

    def build_prompt(
        self,
        tracker: Tracker,
        memoria: str,
        perfil: str,
    ) -> str:
        raw_msg = tracker.latest_message.get("text", "")
        clean_msg = normalize_chat_text(raw_msg)
        user_msg = anonymize_text(clean_msg)
        intent_info = tracker.latest_message.get("intent", {})

        # historial corto (máx 6 turnos)
        history: List[str] = []
        for e in tracker.events[-12:]:
            if e.get("event") == "user":
                history.append("Usuario: " + anonymize_text(e.get("text", "")))
            elif e.get("event") == "bot":
                history.append("Bot: " + str(e.get("text", "")))

        hist_text = "\n".join(history[-6:])

        prompt = (
            PROMPT_SYSTEM
            + f"\n\n=== PERFIL DETECTADO ===\n{perfil}\n"
            + f"\n=== MEMORIA SEMÁNTICA ===\n{memoria}\n"
            + "\n=== CONTEXTO DE LA CONVERSACIÓN ===\n"
            + f"Último mensaje del usuario: {user_msg}\n"
            + f"Intent detectado por Rasa: {intent_info.get('name')} "
            + f"(conf={intent_info.get('confidence')})\n"
            + f"Historial breve:\n{hist_text}\n"
            + "\nResponde ÚNICAMENTE en formato:\n"
            + "INTENT:<nombre_intent>  o  RESPUESTA:<texto>\n"
        )
        return prompt

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        raw_msg = tracker.latest_message.get("text", "")
        clean_msg = normalize_chat_text(raw_msg)

        prev = retrieve_similar(clean_msg)
        if prev:
            memoria = f"Continuación del tema anterior: {prev['text']}"
        else:
            memoria = "Nuevo tema."

        store_message(clean_msg)
        perfil = detectar_materia(clean_msg)
        prompt = self.build_prompt(tracker, memoria, perfil)
        logger.info(f"[LLM PROMPT] {prompt[:400]}...")

        raw = call_ollama(prompt)

        if not raw:
            dispatcher.utter_message(
                text="No puedo procesar tu solicitud en este momento. ¿Podrías reformularla?"
            )
            return []

        parsed = parse_llm_response(raw)
        logger.info(f"[LLM PARSED] {parsed}")

        if parsed["type"] == "intent":
            intent_name = parsed["value"]
            logger.info(f"[LLM] Intent sugerido: {intent_name}")

            return [
                SlotSet("llm_suggested_intent", intent_name),
                SlotSet("from_llm", True),
                FollowupAction("action_route_llm_intent"),
            ]

        if parsed["type"] == "response":
            dispatcher.utter_message(text=parsed["value"])
            return [SlotSet("from_llm", True)]

        dispatcher.utter_message(text=parsed["value"])
        return [SlotSet("from_llm", True)]


class ActionRouteLLMIntent(Action):
    def name(self) -> Text:
        return "action_route_llm_intent"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        suggested = tracker.get_slot("llm_suggested_intent")

        if not suggested:
            dispatcher.utter_message(
                text="No pude identificar claramente tu intención. ¿Podrías explicarme un poco más qué necesitas?"
            )
            return []

        suggested = str(suggested).strip()
        logger.info(f"[LLM ROUTER] llm_suggested_intent = {suggested}")

        SYSTEM_INTENT_TO_ACTION: Dict[str, str] = {
            # 📄 CERTIFICADOS
            "consultar_certificados": "action_consultar_certificados",
            "solicitar_certificado": "action_consultar_certificados",

            # 🆘 SOPORTE
            "soporte_acceso": "soporte_form",
            "solicitar_soporte": "soporte_form",

            # 🔐 LOGIN / RECUPERAR
            "auth_login_cmd": "auth_login_form",
            "recuperar_contrasena": "password_recovery_form",
            "confirmar_autenticacion": "action_set_authenticated_true",
            "negar_autenticacion": "action_set_authenticated_true",

            # 📋 ENCUESTA
            "respuesta_satisfecho": "encuesta_satisfaccion_form",
            "respuesta_insatisfecho": "encuesta_satisfaccion_form",

            # 📂 MENÚ / NAVEGACIÓN
            "ir_menu_principal": "action_ir_menu_principal",
            "limpiar_sesion": "action_reiniciar_conversacion",
            "ping_servidor": "action_ping_servidor",

            # 🔁 AUTOSAVE / REANUDAR
            "reanudar_auto_si": "action_reanudar_auto",
            "reanudar_auto_no": "action_ir_menu_principal",
            "limpiar_autosave": "action_cancelar_cierre_autosave",

            # 🔚 CIERRE
            "confirmar_cierre": "action_confirmar_cierre",
            "cancelar_cierre": "action_cancelar_cierre",
            "confirmar_cierre_seguro": "action_confirmar_cierre_seguro",
            "confirmar_cierre_seguro_final": "action_confirmar_cierre_autosave",

            # 👤 HUMANO / HANDOFF
            "solicitar_humano": "action_ofrecer_humano",
            "confirmar_derivacion_humano": "action_derivar_humano_confirmada",
            "cancelar_derivacion": "action_cancelar_derivacion",
        }

        if suggested in SYSTEM_INTENT_TO_ACTION:
            action_name = SYSTEM_INTENT_TO_ACTION[suggested]
            logger.info(f"[LLM ROUTER] Intent de sistema '{suggested}' -> '{action_name}'")

            return [
                FollowupAction(action_name),
                SlotSet("llm_suggested_intent", None),
                SlotSet("from_llm", False),
            ]

        responses = domain.get("responses", {})
        utter_name = f"utter_{suggested}"

        events: List[Dict[Text, Any]] = [
            SlotSet("tema_previsto", suggested),
            SlotSet("llm_suggested_intent", None),
            SlotSet("from_llm", False),
        ]

        if utter_name in responses:
            logger.info(f"[LLM ROUTER] Encontrado utter específico: {utter_name}")
            events.insert(0, FollowupAction(utter_name))
        else:
            logger.info(f"[LLM ROUTER] Tema académico genérico, sin utter específico: {suggested}")
            dispatcher.utter_message(
                text="Perfecto, sigamos con ese tema. Te lo explicaré paso a paso de forma clara."
            )

        events.append(FollowupAction("action_handle_with_llm"))
        return events


class ActionMemoryWrapper(Action):
    def name(self) -> Text:
        return "action_memory_wrapper"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        user_msg = tracker.latest_message.get("text", "")

        if not user_msg:
            return []

        prev = retrieve_similar(user_msg)

        if prev:
            logger.info(f"[MEMORIA] Mensaje similar encontrado: {prev['text']}")
            # Si quisieras avisar al usuario, puedes activar esto:
            # dispatcher.utter_message(
            #     text=f"Veo que estás retomando un tema relacionado con: '{prev['text']}'"
            # )

        store_message(user_msg)
        logger.info(f"[MEMORIA] Mensaje almacenado: {user_msg}")

        return []


class ActionResumenSesionLLM(Action):
    """
    Genera un resumen amable de la sesión actual, SIN inventar datos sensibles.
    Usa solo slots y eventos ya ocurridos, y los pasa por llm_summarize_with_ollama
    para mejorar redacción.
    """

    def name(self) -> Text:
        return "action_resumen_sesion_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        temas: List[str] = []

        # ¿Hubo soporte?
        motivo = tracker.get_slot("motivo_soporte")
        tipo_soporte = tracker.get_slot("tipo_soporte")
        if motivo or tipo_soporte:
            if tipo_soporte == "pqrs":
                temas.append("Se registró una solicitud de PQRS o soporte formal.")
            elif tipo_soporte == "interno":
                temas.append("Se registró una solicitud de soporte interno en la plataforma.")
            else:
                temas.append("Hablamos sobre un problema técnico o de acceso a la plataforma.")

        # ¿Hubo consulta académica?
        if _is_auth(tracker):
            temas.append("Consultaste información académica personalizada (estado y/o certificados).")
        else:
            # Usuario sin auth que preguntó por academia
            try:
                latest_intent = (
                    tracker.get_intent_of_latest_message()
                    if hasattr(tracker, "get_intent_of_latest_message")
                    else (tracker.latest_message.get("intent") or {}).get("name")
                )
            except Exception:
                latest_intent = (tracker.latest_message.get("intent") or {}).get("name")

            if latest_intent in [
                "estado_estudiante",
                "ver_estado_estudiante",
                "consultar_certificados",
                "ver_certificados",
            ]:
                temas.append(
                    "Revisamos cómo consultar tu estado académico o certificados desde la plataforma."
                )

        # ¿Encuesta de satisfacción?
        nivel_satisfaccion = tracker.get_slot("nivel_satisfaccion")
        if nivel_satisfaccion:
            temas.append(
                f"Completaste una encuesta de satisfacción y calificaste la atención como: {nivel_satisfaccion}."
            )
        elif tracker.get_slot("encuesta_incompleta"):
            temas.append("Iniciaste una encuesta de satisfacción que quedó pendiente.")

        # Tema académico genérico
        tema_actual = tracker.get_slot("tema_actual") or tracker.get_slot("tema_previsto")
        if tema_actual:
            temas.append(f"Conversamos sobre el tema académico: {tema_actual}.")

        if not temas:
            temas.append("Tuviste una sesión breve de consulta con el asistente Zajuna.")

        texto_base = "Resumen de tu sesión con el asistente Zajuna:\n"
        for t in temas:
            texto_base += f"- {t}\n"

        texto_base += (
            "\nEn la siguiente sesión, podrás retomar estos temas o iniciar nuevas consultas "
            "sobre tu formación, soporte técnico o trámites académicos."
        )

        contexto_llm = {
            "flujo": "resumen_sesion",
            "tuvo_soporte": bool(motivo or tipo_soporte),
            "tuvo_encuesta": bool(nivel_satisfaccion),
            "autenticado": _is_auth(tracker),
        }

        try:
            mensaje = llm_summarize_with_ollama(texto_base, contexto_llm)
        except Exception:
            logger.exception("Error generando resumen de sesión con LLM.")
            mensaje = texto_base

        dispatcher.utter_message(text=mensaje)
        return []

class ActionIncrementarTurnosConversacion(Action):
    """
    Incrementa el contador de turnos de conversación y marca la sesión como 'larga'
    cuando supera cierto umbral (por defecto 8 turnos).

    No toca ningún dato sensible, solo slots métricos.
    """

    UMBRAL_SESION_LARGA = int(os.getenv("SESION_LARGA_UMBRAL", "8"))

    def name(self) -> Text:
        return "action_incrementar_turnos_conversacion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        actual = tracker.get_slot("turnos_conversacion") or 0

        try:
            actual_int = int(actual)
        except Exception:
            actual_int = 0

        nuevo_valor = min(actual_int + 1, 9999)

        sesion_larga = tracker.get_slot("sesion_larga")
        sesion_larga_bool = bool(sesion_larga)

        # Si aún no estaba marcada como larga y superamos el umbral → la marcamos
        if not sesion_larga_bool and nuevo_valor >= self.UMBRAL_SESION_LARGA:
            sesion_larga_bool = True

        return [
            SlotSet("turnos_conversacion", nuevo_valor),
            SlotSet("sesion_larga", sesion_larga_bool),
        ]
