import os
import json
import numpy as np
from typing import List, Dict

EMBED_FILE = "semantic_memory.json"


def load_memory() -> List[Dict]:
    if not os.path.exists(EMBED_FILE):
        return []
    with open(EMBED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(mem):
    with open(EMBED_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)


# Simple embedding usando palabras — Opcional sustituir por modelo real
def embed(text: str):
    # embedding simple tipo TF-IDF normalized
    words = text.lower().split()
    vec = {}
    for w in words:
        vec[w] = vec.get(w, 0) + 1
    arr = np.array(list(vec.values()), dtype=float)
    norm = np.linalg.norm(arr)
    return arr / norm if norm else arr


def cosine(a, b):
    if len(a) != len(b):
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def store_message(text: str):
    mem = load_memory()
    mem.append({
        "text": text,
        "embedding": embed(text).tolist()
    })
    save_memory(mem)


def retrieve_similar(text: str, threshold=0.60):
    mem = load_memory()
    query = embed(text)
    best = None
    best_score = 0
    for m in mem:
        e = np.array(m["embedding"])
        score = cosine(query, e)
        if score > best_score:
            best = m
            best_score = score
    return best if best_score >= threshold else None
