# ruta: rasa/actions/actions_semantic_memory.py
from __future__ import annotations
import redis
import json
import logging
import math
import os
from typing import Optional, Dict, Any
from utils.mongo_semantic_memory import collection
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

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=6379,
    decode_responses=True
)
# ============================================================
# STORAGE
# ============================================================

def load_memory() -> list[dict]:  # MEJORA: Uso de tipado nativo list[dict]
    """
    Carga la memoria semántica local desde el archivo JSON.
    Tolera archivos inexistentes o corruptos retornando una lista vacía.
    """
    if not os.path.exists(EMBED_FILE):
        save_memory([])
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
        logger.warning(
            "[SEMANTIC_MEMORY] embedding unavailable"
        )
        return None


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
        logger.warning(
            "[SEMANTIC_MEMORY] embedding unavailable"
        )
        return None


# ============================================================
# STORE
# ============================================================

def store_message(
    text: str,
    user_id: str | None = None,
    session_id: str | None = None,
    metadata: Dict[str, Any] | None = None
) -> None:

    try:
        # 1. Normalización
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
            logger.warning("[SEMANTIC_MEMORY] normalize failed")
            normalized = text

        # 2. Embedding
        emb = get_embedding(normalized)

        # 3. Record Mongo
        record = {
            "user_id": user_id,
            "session_id": session_id,
            "text": text,
            "text_original": text,
            "text_normalized": normalized,
            "metadata": metadata or {},
            "embedding": emb
        }

        if emb is None:
            record.pop("embedding", None)

        # 4. INSERT DIRECTO (IMPORTANTE)
        collection.insert_one(record)

    except Exception:
        logger.exception("[SEMANTIC_MEMORY] store_message failed")


# ============================================================
# RETRIEVE
# ============================================================

def retrieve_similar(
    text: str,
    user_id: str | None = None,
    session_id: str | None = None,
    threshold: float = 0.60
) -> Optional[dict]:

    try:

        if not session_id:
            session_id = user_id

        if not session_id:
            session_id = "anonymous"


        # ====================================================
        # REDIS CACHE
        # ====================================================

        cache_key = f"mem:{user_id}:{session_id}:{text}"

        cached = redis_client.get(cache_key)

        if cached:
            logger.info(
                "[SEMANTIC_MEMORY] Redis cache HIT"
            )
            return json.loads(cached)


        # ====================================================
        # MONGO QUERY
        # ====================================================

        query_filter = {}

        if user_id:
            query_filter["user_id"] = user_id

        if session_id:
            query_filter["session_id"] = session_id


        mem = list(
            collection.find(query_filter)
            .limit(200)
        )


        if not mem:
            return None



        # ====================================================
        # NORMALIZACIÓN
        # ====================================================

        try:
            resp = requests.post(
                NORMALIZE_URL,
                json={"text": text},
                timeout=5.0,
            )

            resp.raise_for_status()

            data = resp.json()

            query_norm = (
                data.get("normalized")
                or text
            )

        except Exception:

            logger.warning(
                "[SEMANTIC_MEMORY] normalize unavailable"
            )

            query_norm = text



        # ====================================================
        # EMBEDDING QUERY
        # ====================================================

        query_emb = get_embedding(query_norm)


        best = None
        best_score = 0.0


        has_embeddings = any(
            m.get("embedding")
            for m in mem
        )



        # ====================================================
        # COSENO
        # ====================================================

        if query_emb is not None and has_embeddings:

            for m in mem:

                emb = m.get("embedding")

                if not emb:
                    continue


                score = cosine(
                    query_emb,
                    emb
                )


                if score > best_score:

                    best_score = score
                    best = m



        # ====================================================
        # FALLBACK JACCARD
        # ====================================================

        else:

            for m in mem:

                stored = (
                    m.get("text_normalized")
                    or m.get("text", "")
                )


                score = jaccard_similarity(
                    query_norm,
                    stored
                )


                if score > best_score:

                    best_score = score
                    best = m



        # ====================================================
        # GUARDAR EN REDIS
        # ====================================================

        if best_score >= threshold and best:

            redis_client.setex(
                cache_key,
                300,
                json.dumps(
                    best,
                    default=str
                )
            )


            logger.info(
                "[SEMANTIC_MEMORY] Redis cache SET"
            )


            return best



        return None



    except Exception:

        logger.exception(
            "[SEMANTIC_MEMORY] retrieve_similar failed"
        )

        return None