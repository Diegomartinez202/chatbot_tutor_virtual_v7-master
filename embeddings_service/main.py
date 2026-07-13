from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
import numpy as np

app = FastAPI(title="Embedding Service", version="0.1.0")

# ---------- MODELOS ----------

class TextRequest(BaseModel):
    text: str

class NormalizeResponse(BaseModel):
    normalized: str

class EmbedRequest(BaseModel):
    text: str

class EmbedResponse(BaseModel):
    vector: List[float]


# ---------- NORMALIZACIÓN ----------

def normalize_chat_text(text: str) -> str:
    t = text.strip().lower()

    replacements = {
        "holo": "hola",
        "holi": "hola",
        "holaa": "hola",
        "holaaa": "hola",
        "hala": "hola",
        "hla": "hola",
        "ola": "hola",
        "kiero": "quiero",
        "qiero": "quiero",
        "pantalla bnca": "pantalla blanca",
        "pantalla bnka": "pantalla blanca",
    }

    for wrong, right in replacements.items():
        t = t.replace(wrong, right)

    while "  " in t:
        t = t.replace("  ", " ")

    return t


@app.post("/api/normalize", response_model=NormalizeResponse)
async def normalize(req: TextRequest):
    return {"normalized": normalize_chat_text(req.text)}

@app.post("/{path:path}")
async def debug(path: str, request: Request):
    body = await request.body()
    print("PATH:", path)
    print("BODY:", body)
    print("HEADERS:", request.headers)
    return {"error": "debug"}
# ---------- EMBEDDINGS ----------

def dummy_embed(text: str) -> np.ndarray:
    words = text.lower().split()
    vec = {}
    for w in words:
        vec[w] = vec.get(w, 0) + 1
    arr = np.array(list(vec.values()), dtype=float)
    norm = np.linalg.norm(arr)
    return arr / norm if norm else arr


@app.post("/api/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest):
    vector = dummy_embed(req.text)
    return EmbedResponse(vector=vector.tolist())

@app.get("/health")
def health():
    return {
        "status": "ok"
    }