import os
import json
import numpy as np
from typing import List, Dict

# Archivo de memoria semántica en disco
EMBED_FILE = "semantic_memory.json"


def load_memory() -> List[Dict]:
    """Carga la memoria semántica desde semantic_memory.json."""
    if not os.path.exists(EMBED_FILE):
        return []
    with open(EMBED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(mem: List[Dict]) -> None:
    """Guarda la memoria semántica en semantic_memory.json."""
    with open(EMBED_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)


def embed(text: str) -> np.ndarray:
    """
    Embedding simple tipo bolsa de palabras normalizada.
    NO es un modelo real, solo sirve como similitud básica.
    """
    words = text.lower().split()
    vec = {}
    for w in words:
        vec[w] = vec.get(w, 0) + 1
    arr = np.array(list(vec.values()), dtype=float)
    norm = np.linalg.norm(arr)
    return arr / norm if norm else arr


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Similitud coseno entre dos vectores."""
    if a.size == 0 or b.size == 0:
        return 0.0
    if len(a) != len(b):
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def store_message(text: str) -> None:
    """
    Guarda el mensaje en memoria semántica incluyendo:
    - texto original
    - texto normalizado
    - embedding basado en el texto normalizado

    Además mantiene el campo 'text' por compatibilidad hacia atrás.
    """
    # Import perezoso para evitar import circular con acciones_llm
    from .acciones_llm import normalize_chat_text

    mem = load_memory()

    normalized = normalize_chat_text(text)
    emb = embed(normalized)

    mem.append(
        {
            # Compatibilidad con código antiguo que espera m["text"]
            "text": text,
            # Nuevo esquema enriquecido:
            "text_original": text,
            "text_normalized": normalized,
            "embedding": emb.tolist(),
        }
    )

    save_memory(mem)


def retrieve_similar(text: str, threshold: float = 0.60):
    """
    Recupera el mensaje más similar al texto dado.
    - Normaliza la query antes de hacer el embedding.
    - Usa similitud coseno sobre los embeddings.
    """
    # Import perezoso para evitar import circular
    from .acciones_llm import normalize_chat_text

    mem = load_memory()
    if not mem:
        return None

    query_norm = normalize_chat_text(text)
    query_emb = embed(query_norm)

    best = None
    best_score = 0.0

    for m in mem:
        e = np.array(m["embedding"], dtype=float)
        score = cosine(query_emb, e)
        if score > best_score:
            best = m
            best_score = score

    return best if best_score >= threshold else None
