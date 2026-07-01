# ruta: rasa/actions/core/nlp_utils.py
from __future__ import annotations

import logging
import re
from typing import Optional

from rapidfuzz import fuzz

from .prompts import MATERIAS

logger = logging.getLogger(__name__)

# ================================================================
# 📧 REGEX COMPILADAS EN SCOPE GLOBAL (OPTIMIZACIÓN DE CPU)
# ================================================================
# CORRECCIÓN: Patrones precompilados para evitar re-compilación en cada petición del usuario
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
ANONYMIZE_EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# Detecta cadenas numéricas largas aisladas (ej: Cédulas de ciudadanía, teléfonos o códigos de ruta)
ANONYMIZE_NUM_REGEX = re.compile(r"\b\d{8,}\b")
WHITESPACE_REGEX = re.compile(r"\s+")

# ================================================================
# 📧 EMAIL VALIDATION
# ================================================================
def is_valid_email(email: str) -> bool:
    """
    Valida si una cadena cumple estructuralmente con el formato de correo electrónico.
    """
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip().lower()))


# ================================================================
# 🧼 TEXT CLEANING
# ================================================================
def clean_text(text: str) -> str:
    """
    Remueve saltos de línea destructivos y colapsa espacios en blanco consecutivos.
    """
    if not text:
        return ""
    return WHITESPACE_REGEX.sub(" ", text).strip()


# ================================================================
# 🔢 SAFE INT
# ================================================================
def safe_int(value: str, default: int = 0) -> int:
    """
    Castea de forma segura strings a enteros mitigando excepciones por valores alfanuméricos.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


# ================================================================
# 📚 MATERIA DETECTION (FUZZY MATCHING INTERNO)
# ================================================================
def normalize_text(text: str) -> str:
    """Normaliza texto para igualar condiciones de comparación léxica."""
    if not text:
        return ""
    return clean_text(text).lower()


def detectar_materia(text: str) -> str:
    """
    Clasifica de forma difusa el texto del estudiante contra el catálogo global
    de asignaturas del SENA (MATERIAS). Si el ratio de similitud supera el 75%,
    asigna la materia correspondiente; de lo contrario, aplica fallback temático general.
    """
    if not text:
        return "tema academico"

    normalized_input = normalize_text(text)

    mejor_materia: Optional[str] = None
    best_score = 0

    # Iteración ágil sobre los diccionarios de asignaturas predefinidas
    for materia in MATERIAS.keys():
        materia_norm = normalize_text(materia)
        
        # Métrica de razón parcial: ideal para detectar sub-frases en oraciones de chat
        actual_score = fuzz.partial_ratio(normalized_input, materia_norm)

        if actual_score > best_score:
            best_score = int(actual_score)
            mejor_materia = materia

    if best_score >= 75 and mejor_materia is not None:
        return mejor_materia

    return "tema academico"


# ================================================================
# 🔒 ANONYMIZER (DATA PRIVACY LAYER)
# ================================================================
def anonymize_text(text: str) -> str:
    """
    Sanitiza y ofusca datos de identificación personal (PII) antes de que 
    la consulta del estudiante sea transmitida al core de inferencia LLM.
    """
    if not text:
        return text

    # Sustitución veloz utilizando las expresiones precompiladas globales
    text = ANONYMIZE_EMAIL_REGEX.sub("[EMAIL]", text)
    text = ANONYMIZE_NUM_REGEX.sub("[NUM]", text)
    
    return text