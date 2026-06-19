# ruta: rasa/actions/actions_semantic_memory.py
from __future__ import annotations

import json
import logging
import math  # MEJORA: Movido al scope global para optimizar las iteraciones en caliente
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)

EMBED_FILE = os.getenv(
    "SEMANTIC_MEMORY_FILE",
    "/app/data/semantic_memory.json"
)
EMBEDDING_BASE = "http://embedding-service:9000"

NORMALIZE_URL = f"{EMBEDDING_BASE}/api/normalize"
EMBED_URL = f"{EMBEDDING_BASE}/api/embed"

MAX_MEMORY_RECORDS = 5000


# ============================================================
# STORAGE
# ============================================================

def load_memory() -> list[dict]:  # MEJORA: Uso de tipado nativo list[dict]
    """
    Carga la memoria semántica local desde el archivo JSON.
    Tolera archivos inexistentes o corruptos retornando una lista vacía.
    """
    if not os.path.exists(EMBED_FILE):
        return []

    try:
        with open(
            EMBED_FILE,
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        return data if isinstance(data, list) else []

    except Exception:
        logger.exception("[SEMANTIC_MEMORY] load_memory failed")
        return []


def save_memory(mem: list[dict]) -> None:  # MEJORA: Uso de tipado nativo list[dict]
    """
    Realiza un guardado atómico utilizando un archivo temporal intermedio.
    Previene la corrupción del JSON si el contenedor Docker se detiene abruptamente.
    """
    try:
        tmp_file = EMBED_FILE + ".tmp"

        with open(
            tmp_file,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                mem,
                f,
                indent=2,
                ensure_ascii=False,
            )

        os.replace(tmp_file, EMBED_FILE)

    except Exception:
        logger.exception("[SEMANTIC_MEMORY] save_memory failed")


# ============================================================
# SIMILARITY
# ============================================================

def jaccard_similarity(a: str, b: str) -> float:
    """
    Calcula el índice de similitud de Jaccard entre dos cadenas de texto tokens.
    Actúa como el algoritmo de respaldo ante fallas del servicio de embeddings.
    """
    sa = set(a.split())
    sb = set(b.split())

    if not sa and not sb:
        return 0.0

    inter = len(sa & sb)
    union = len(sa | sb)

    return inter / union if union else 0.0


def cosine(a: list[float], b: list[float]) -> float:
    """
    Calcula la similitud del coseno entre dos vectores densos.
    Añade un épsilon de protección contra divisiones por cero.
    """
    if not a or not b:
        return 0.0

    if len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))

    # MEJORA: Validación defensiva contra vectores de magnitudes nulas
    if na == 0.0 or nb == 0.0:
        return 0.0

    return dot / (na * nb + 1e-9)


# ============================================================
# EMBEDDINGS
# ============================================================

def get_embedding(text: str) -> Optional[list[float]]:
    """
    Solicita el vector de embedding al microservicio externo.
    """
    try:
        resp = requests.post(
            EMBED_URL,
            json={"text": text},
            timeout=5.0,
        )
        resp.raise_for_status()
        data = resp.json()
        vec = data.get("vector")

        if isinstance(vec, list):
            return vec

        return None

    except Exception:
        logger.exception("[SEMANTIC_MEMORY] embedding failed")
        return None


# ============================================================
# STORE
# ============================================================

def store_message(text: str) -> None:
    """
    Normaliza, extrae el embedding y almacena de forma indexada
    un nuevo registro de conversación respetando el límite superior de registros.
    """
    try:
        mem = load_memory()

        try:
            resp = requests.post(
                NORMALIZE_URL,
                json={"text": text},
                timeout=5.0,
            )
            resp.raise_for_status()
            data = resp.json()
            normalized = data.get("normalized") or data.get("text") or text

        except Exception:
            logger.exception("[SEMANTIC_MEMORY] normalize failed")
            normalized = text

        emb = get_embedding(normalized)

        record = {
            "text": text,
            "text_original": text,
            "text_normalized": normalized,
        }

        if emb is not None:
            record["embedding"] = emb

        mem.append(record)

        # Evita crecimiento infinito de memoria en disco (FIFO Slicing)
        if len(mem) > MAX_MEMORY_RECORDS:
            mem = mem[-MAX_MEMORY_RECORDS:]

        save_memory(mem)

    except Exception:
        logger.exception("[SEMANTIC_MEMORY] store_message failed")


# ============================================================
# RETRIEVE
# ============================================================

def retrieve_similar(text: str, threshold: float = 0.60) -> Optional[dict]:
    """
    Busca el registro más cercano en la memoria semántica utilizando la estrategia
    disponible (Similitud de Coseno si hay embeddings o Jaccard como contingencia).
    """
    try:
        mem = load_memory()
        if not mem:
            return None

        try:
            resp = requests.post(
                NORMALIZE_URL,
                json={"text": text},
                timeout=5.0,
            )
            resp.raise_for_status()
            data = resp.json()
            query_norm = data.get("normalized") or text

        except Exception:
            logger.exception("[SEMANTIC_MEMORY] query normalize failed")
            query_norm = text

        query_emb = get_embedding(query_norm)
        best = None
        best_score = 0.0

        has_embeddings = any("embedding" in m for m in mem)

        # Estrategia A: Comparación Semántica Vectorial (Coseno)
        if query_emb is not None and has_embeddings:
            for m in mem:
                emb = m.get("embedding")
                if not emb:
                    continue

                score = cosine(query_emb, emb)
                if score > best_score:
                    best_score = score
                    best = m

        # Estrategia B: Respaldo por Léxico Distribuído (Jaccard)
        else:
            for m in mem:
                stored_norm = m.get("text_normalized") or m.get("text", "")
                score = jaccard_similarity(query_norm, stored_norm)
                if score > best_score:
                    best_score = score
                    best = m

        if best_score >= threshold:
            return best

        return None

    except Exception:
        logger.exception("[SEMANTIC_MEMORY] retrieve_similar failed")
        return None