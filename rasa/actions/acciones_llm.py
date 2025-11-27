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
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "15"))


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


def normalize_chat_text(text: str) -> str:
    """
    Normaliza texto de usuario para que el bot entienda aunque escriba
    con errores: tildes, letras repetidas, abreviaturas típicas de chat.
    """
    if not text:
        return ""

    # 1) Minúsculas + quitar tildes (reusa tu normalize)
    t = normalize(text)

    # 2) Colapsar letras repetidas: "holaaaa" -> "hola"
    #    dejamos máximo 2 repeticiones para no matar expresividad
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)

    # 3) Reemplazos directos de jerga / typos frecuentes
    for wrong, right in COMMON_CHAT_CORRECTIONS.items():
        t = t.replace(wrong, right)

    # 4) Limpieza básica de espacios
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

def detectar_materia(text: str) -> str:
    # Antes: t = normalize(text)
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

    except Exception:
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
        value = m_resp.group(1).strip()
        # Si por alguna razón el modelo mezcla cosas, cortamos si aparece un INTENT después
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


# ==========================================================
# 🎯 ACCIÓN PRINCIPAL: ActionHandleWithOllama
# ==========================================================
class ActionHandleWithOllama(Action):
    def name(self) -> Text:
        return "action_handle_with_llm"

    def build_prompt(
        self,
        tracker: Tracker,
        memoria: str,
        perfil: str
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

    # ---- Ejecución principal ----
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Texto actual del usuario
        raw_msg = tracker.latest_message.get("text", "")
        clean_msg = normalize_chat_text(raw_msg)

        # 1) Buscar si ya se habló de lo mismo (memoria semántica) con texto limpio
        prev = retrieve_similar(clean_msg)
        if prev:
            memoria = f"Continuación del tema anterior: {prev['text']}"
        else:
            memoria = "Nuevo tema."

        # 2) Guardar en memoria el mensaje normalizado
        store_message(clean_msg)

        # 3) Detectar materia / perfil didáctico con texto limpio
        perfil = detectar_materia(clean_msg)

        # 4) Construir prompt completo (build_prompt solo usa estos valores)
        prompt = self.build_prompt(tracker, memoria, perfil)
        logger.info(f"[LLM PROMPT] {prompt[:400]}...")

        # 5) Llamar a Ollama
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
            intent_name = parsed["value"]
            logger.info(f"[LLM] Intent sugerido: {intent_name}")

            return [
                SlotSet("llm_suggested_intent", intent_name),
                SlotSet("from_llm", True),
                FollowupAction("action_route_llm_intent"),
            ]

        # --- Si es texto explicativo (RESPUESTA) ---
        if parsed["type"] == "response":
            dispatcher.utter_message(text=parsed["value"])
            return [SlotSet("from_llm", True)]

        # --- Raw fallback ---
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
            # Si por alguna razón no hay intent sugerido, hacer fallback suave
            dispatcher.utter_message(
                text="No pude identificar claramente tu intención. ¿Podrías explicarme un poco más qué necesitas?"
            )
            return []

        # Normalizar
        suggested = str(suggested).strip()
        logger.info(f"[LLM ROUTER] llm_suggested_intent = {suggested}")

        # 1) INTENTS DE SISTEMA -> acciones concretas
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

        # 2) TEMAS ACADÉMICOS / GENÉRICOS -> no exigimos utter_ por cada uno
        responses = domain.get("responses", {})  # dict con utter_... si existen
        utter_name = f"utter_{suggested}"

        events: List = [
            SlotSet("tema_previsto", suggested),
            SlotSet("llm_suggested_intent", None),
            SlotSet("from_llm", False),
        ]

        if utter_name in responses:
            # Si existe un utter específico para este tema, lo usamos como UX
            logger.info(f"[LLM ROUTER] Encontrado utter específico: {utter_name}")
            events.insert(0, FollowupAction(utter_name))
        else:
            # Sin utter específico -> UX genérica + seguimos con el LLM
            logger.info(f"[LLM ROUTER] Tema académico genérico, sin utter específico: {suggested}")
            dispatcher.utter_message(
                text="Perfecto, sigamos con ese tema. Te lo explicaré paso a paso de forma clara."
            )

        # Luego volvemos a mandar al LLM para que desarrolle el tema
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
            # Nada que guardar
            return []

        # 1) Buscar mensaje similar en la memoria semántica
        prev = retrieve_similar(user_msg)

        if prev:
            logger.info(f"[MEMORIA] Mensaje similar encontrado: {prev['text']}")
            # Si quisieras avisar al usuario, puedes activar esto:
            dispatcher.utter_message(
                text=f"Veo que estás retomando un tema relacionado con: '{prev['text']}'"
            )

        # 2) Guardar el mensaje actual en la memoria
        store_message(user_msg)
        logger.info(f"[MEMORIA] Mensaje almacenado: {user_msg}")

        # Aquí opcionalmente puedes setear algún slot como 'tema_previsto'
        # o 'historial_academico', según tu lógica
        return []