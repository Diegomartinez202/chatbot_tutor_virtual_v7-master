# ruta: rasa/actions/text_normalization.py
from __future__ import annotations

import re
import unicodedata

# MEJORA: Diccionario unificado global para evitar sobrecostos por recreación en cada llamada
COMMON_CHAT_CORRECTIONS: dict[str, str] = {
    "k": "que",
    "q": "que",
    "qe": "que",
    "qer": "querer",
    "kiero": "quiero",
    "kiere": "quiere",
    "kieres": "quieres",
    "pa": "para",
    "xq": "porque",
    "xk": "porque",
    "xk?": "porque",
    "aprnder": "aprender",
    "certifcado": "certificado",
    "certifcados": "certificados",
    "sertificado": "certificado",
    "sertificados": "certificados",
    "logaer": "lograr",
    "loguearme": "loguearme",
    "loguear": "loguear",
    "contraseña": "contrasena",
    "platafroma": "plataforma",
    "platafomra": "plataforma",
    "markeitng": "marketing",
    "markting": "marketing",
    "digitla": "digital",
}


def normalize(text: str) -> str:
    """
    Convierte a minúsculas y remueve caracteres combinatorios de acentuación (tildes).
    """
    # CORRECCIÓN: Corrección de sangría y validación segura contra valores nulos o vacíos
    if not text:
        return ""

    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    ).lower()


def strip_accents(text: str) -> str:
    """
    Remueve acentos preservando la caja del texto (Mayúsculas/Minúsculas).
    """
    if not text:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


def normalize_chat_text(text: str) -> str:
    """
    Normaliza texto de usuario para que el bot entienda aunque escriba
    con errores típicos de redes sociales o chats:
    - Eliminación de tildes.
    - Compresión de letras repetidas (ej: "holaaaa" -> "holaa").
    - Estandarización de risas y abreviaturas.
    """
    if not text:
        return ""

    # 1. Quitar tildes y homogeneizar a minúsculas
    t = normalize(text)

    # 2. CORRECCIÓN: Separación de re.sub mal estructurados que rompían el compilador
    # Reduce caracteres idénticos repetidos más de 2 veces (ej. "siiiii" -> "sii")
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)
    
    # Estandariza ráfagas de risas en el chat
    t = re.sub(r"(ja){3,}", "jajaja", t)

    # 3. Tokenización y mapeo de modismos/jerga
    tokens = t.split()
    normalized_tokens = [COMMON_CHAT_CORRECTIONS.get(tok, tok) for tok in tokens]

    # 4. Reconstrucción y remoción de espacios colaterales residuales
    t = " ".join(normalized_tokens)
    t = re.sub(r"\s+", " ", t).strip()
    
    return t