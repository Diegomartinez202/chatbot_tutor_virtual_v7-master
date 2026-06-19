"""
DEPRECATED

Sustituido por:
core/orchestrator_v2.py

No usar en producción.
Pendiente eliminación después de validar:

domain.yml
rules.yml
stories.yml
nlu.yml
"""

from typing import Dict, Any, Optional
ROUTE_CERTIFICADOS = "certificados"
ROUTE_HORARIOS = "horarios"
ROUTE_PROGRESO = "progreso"
ROUTE_TUTOR = "tutor_asignado"
ROUTE_ESTADO = "estado_estudiante"

class LLMRouter:

    def __init__(self):
        # --------------------------------------------------------
        # RULES BASE (fallback determinístico)
        # --------------------------------------------------------
        self.rules = {
            "aprender_tema": "action_explicar_tema_llm",
            "soporte_tecnico": "action_soporte_llm",
            "error_actividad": "action_soporte_llm",
            "consultar_estado": "estado_estudiante",
            "consultar_tutor": "tutor_asignado",
            "consultar_certificados": "certificados",
            "consultar_progreso": "progreso",
            "consultar_horarios": "horarios",
        }

        self.default_action = "action_explicar_tema_llm"

    # ============================================================
    # 🧠 ROUTING INTELIGENTE
    # ============================================================
    def route(
        self,
        intent: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:

        context = context or {}

        # --------------------------------------------------------
        # 1. VALIDACIÓN BÁSICA
        # --------------------------------------------------------
        if not intent:
            return self.default_action

        # --------------------------------------------------------
        # 2. CONTEXTO PRIORITARIO (V2)
        # --------------------------------------------------------
        # Ej: usuario en soporte urgente o flujo académico activo
        if context.get("force_support"):
            return "action_soporte_llm"

        if context.get("force_academic"):
            return ROUTE_PROGRESO
        # --------------------------------------------------------
        # 3. ROUTING DIRECTO POR INTENT
        # --------------------------------------------------------
        if intent in self.rules:
            return self.rules[intent]

        # --------------------------------------------------------
        # 4. SEMÁNTICA BÁSICA (heurística V2)
        # --------------------------------------------------------
        text = context.get("text", "").lower()

        if any(w in text for w in ["certificado", "diploma"]):
            return ROUTE_CERTIFICADOS

        if any(w in text for w in ["horario", "clase", "agenda"]):
            return ROUTE_HORARIOS

        if any(w in text for w in ["progreso", "avance", "porcentaje"]):
            return ROUTE_PROGRESO

        if any(w in text for w in ["tutor", "docente"]):
            return ROUTE_TUTOR

        if any(w in text for w in ["estado", "perfil"]):
            return ROUTE_ESTADO

        # --------------------------------------------------------
        # 5. FALLBACK
        # --------------------------------------------------------
        return self.default_action