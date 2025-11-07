# rasa/api/autosave_guardian_api.py
from __future__ import annotations
import os, datetime
from functools import wraps
from typing import Any, Dict

from flask import Flask, request, jsonify
from pymongo import MongoClient
import jwt

# ===== Config =====
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB", "chatbot_tutor_virtual")
AUTOSAVE_COLLECTION = os.getenv("MONGO_AUTOSAVE_COLLECTION", "autosaves")
SEC_LOGS_COLLECTION = os.getenv("MONGO_SECURITY_LOGS_COLLECTION", "seguridad_logs")

JWT_SECRET   = os.getenv("JWT_SECRET", "change-me-in-prod")
JWT_ALG      = os.getenv("JWT_ALG", "HS256")
JWT_ISSUER   = os.getenv("JWT_ISSUER", "guardian-api")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "zajuna-client")

ALLOWED_ORIGINS = set(filter(None, (os.getenv("GUARDIAN_ALLOWED_ORIGINS", "").split(","))))

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
autosaves = db[AUTOSAVE_COLLECTION]
sec_logs  = db[SEC_LOGS_COLLECTION]

app = Flask(__name__)

# ===== Helpers =====
def _client_ip() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")

def log_event(usuario: str, evento: str, estado: str, detail: Dict[str, Any] | None = None):
    sec_logs.insert_one({
        "usuario": usuario,
        "evento": evento,
        "ip": _client_ip(),
        "fecha_hora": datetime.datetime.utcnow(),
        "estado": estado,
        "detalle": detail or {}
    })

def origin_allowed() -> bool:
    if not ALLOWED_ORIGINS:
        return True
    origin = request.headers.get("Origin") or ""
    return origin in ALLOWED_ORIGINS

def origin_gate(f):
    @wraps(f)
    def w(*a, **k):
        if not origin_allowed():
            log_event("desconocido", "origin_blocked", "error", {"origin": request.headers.get("Origin")})
            return jsonify({"error": "origin_not_allowed"}), 403
        return f(*a, **k)
    return w

def jwt_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            log_event("desconocido", "auth_faltante", "error", {"motivo": "sin_bearer"})
            return jsonify({"error": "Missing Bearer token"}), 401
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALG],
                audience=JWT_AUDIENCE,
                issuer=JWT_ISSUER,
            )
            request.jwt_payload = payload
        except Exception as e:
            log_event("desconocido", "auth_invalido", "error", {"motivo": str(e)})
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return wrapper

def _user_from_token() -> str:
    payload = getattr(request, "jwt_payload", {}) or {}
    return str(payload.get("sub") or payload.get("user") or "desconocido")

# ===== Endpoints =====
@app.route("/autosave", methods=["POST"])
@origin_gate
@jwt_required
def autosave_save():
    usuario = _user_from_token()
    body = request.get_json(force=True, silent=True) or {}
    slots = body.get("slots") or {}
    meta  = body.get("meta")  or {}

    payload = {
        "user_id": usuario,
        "slots": slots,
        "meta": meta,
        "estado": "guardado",
        "updated_at": datetime.datetime.utcnow(),
    }
    autosaves.update_one({"user_id": usuario}, {"$set": payload}, upsert=True)
    log_event(usuario, "autosave_guardar", "ok", {"tamano_slots": len(slots)})
    return jsonify({"ok": True})

@app.route("/get", methods=["GET"])
@origin_gate
@jwt_required
def autosave_get():
    usuario = _user_from_token()
    doc = autosaves.find_one({"user_id": usuario}, {"_id": 0})
    log_event(usuario, "autosave_get", "ok", {"existe": bool(doc)})
    return jsonify({"ok": True, "data": doc})

@app.route("/delete", methods=["DELETE"])
@origin_gate
@jwt_required
def autosave_delete():
    usuario = _user_from_token()
    res = autosaves.delete_one({"user_id": usuario})
    log_event(usuario, "autosave_delete", "ok", {"deleted": res.deleted_count})
    return jsonify({"ok": True, "deleted": res.deleted_count})

@app.route("/notify", methods=["POST"])
@origin_gate
@jwt_required
def autosave_notify():
    usuario = _user_from_token()
    body = request.get_json(force=True, silent=True) or {}
    evento = str(body.get("evento") or "desconocido")
    extra  = body.get("extra") or {}
    log_event(usuario, f"notify_{evento}", "ok", extra)
    return jsonify({"ok": True})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "autosave_guardian_api"})
