# autosave_guardian/app.py
# Flask API para autosaves y eventos con JWT + Mongo
# Proyecto: Chatbot Tutor Virtual Zajuna

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient, errors
import jwt  # PyJWT
from pydantic import BaseModel, Field, ValidationError

# -----------------------------
# Configuración desde entorno
# -----------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
MONGO_DB = os.getenv("MONGO_DB", "chatbot_tutor_virtual")
COL_AUTOSAVES = os.getenv("MONGO_AUTOSAVE_COLLECTION", "autosaves")
COL_SEC_LOGS = os.getenv("MONGO_SECURITY_LOGS_COLLECTION", "seguridad_logs")

JWT_SECRET = os.getenv("JWT_SECRET", "cambia-esto-en-produccion")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_ISSUER = os.getenv("JWT_ISSUER", "guardian-api")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "zajuna-client")
JWT_TTL_MIN = int(os.getenv("JWT_TTL_MIN", "1440"))  # 24h por defecto

ALLOWED_ORIGINS = os.getenv(
    "GUARDIAN_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8080"
).split(",")

# (Opcional) credenciales simples si quieres exigir login
ADMIN_USER = os.getenv("GUARDIAN_ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("GUARDIAN_ADMIN_PASS", "admin123")

# -----------------------------
# App & CORS
# -----------------------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS}}, supports_credentials=True)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("autosave-guardian")

# -----------------------------
# Mongo
# -----------------------------
client: Optional[MongoClient] = None
db = None
col_autosaves = None
col_sec_logs = None

def connect_mongo() -> bool:
    global client, db, col_autosaves, col_sec_logs
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        db = client[MONGO_DB]
        col_autosaves = db[COL_AUTOSAVES]
        col_sec_logs = db[COL_SEC_LOGS]
        log.info(f"✅ Conectado a MongoDB: {MONGO_URI} db={MONGO_DB}")
        return True
    except errors.ConnectionFailure as e:
        log.error(f"❌ Error de conexión con MongoDB: {e}")
        return False

connect_mongo()

# -----------------------------
# Modelos (Pydantic)
# -----------------------------
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class AutosaveIn(BaseModel):
    sender_id: str = Field(..., min_length=1)
    data: Dict[str, Any] = Field(default_factory=dict)

class LogEventIn(BaseModel):
    event_type: str = Field(..., min_length=1)
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict)

# -----------------------------
# Utilidades JWT
# -----------------------------
def make_token(sub: str, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    now = datetime.now(tz=timezone.utc)
    exp = now + timedelta(minutes=JWT_TTL_MIN)
    payload = {
        "sub": sub,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return token

def verify_token(token: str) -> Dict[str, Any]:
    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALG],
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
    )

def auth_required(fn):
    # Decorador simple para rutas protegidas
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify(error="missing_bearer_token"), 401
        token = auth.split(" ", 1)[1].strip()
        try:
            claims = verify_token(token)
            request.jwt_claims = claims  # type: ignore
        except jwt.ExpiredSignatureError:
            return jsonify(error="token_expired"), 401
        except jwt.InvalidTokenError:
            return jsonify(error="invalid_token"), 401
        return fn(*args, **kwargs)
    return wrapper

# -----------------------------
# Healthcheck
# -----------------------------
@app.get("/ping")
def ping():
    ok = client is not None
    return jsonify(ok=ok)

# -----------------------------
# Auth
# -----------------------------
@app.post("/auth/login")
def auth_login():
    try:
        data = LoginRequest(**request.get_json(force=True))
    except ValidationError as ve:
        return jsonify(error="validation_error", details=ve.errors()), 400

    # Lógica mínima: usa credenciales de env (si las cambias en producción).
    if data.username != ADMIN_USER or data.password != ADMIN_PASS:
        return jsonify(error="invalid_credentials"), 401

    token = make_token(sub=data.username, extra_claims={"role": "admin"})
    return jsonify(access_token=token, token_type="Bearer", expires_in_minutes=JWT_TTL_MIN)

@app.get("/auth/verify")
@auth_required
def auth_verify():
    # Si pasó el decorador, el token es válido
    return jsonify(valid=True, claims=getattr(request, "jwt_claims", {}))

# -----------------------------
# Autosaves
# -----------------------------
@app.post("/autosaves")
@auth_required
def create_autosave():
    if col_autosaves is None:
        return jsonify(error="mongo_unavailable"), 503
    try:
        body = AutosaveIn(**request.get_json(force=True))
    except ValidationError as ve:
        return jsonify(error="validation_error", details=ve.errors()), 400

    doc = {
        "sender_id": body.sender_id,
        "data": body.data,
        "timestamp": datetime.utcnow(),
    }
    try:
        res = col_autosaves.insert_one(doc)
        # log de seguridad (no bloqueante)
        try:
            col_sec_logs and col_sec_logs.insert_one({
                "event_type": "autosave_created",
                "sender_id": body.sender_id,
                "ts": datetime.utcnow(),
            })
        except Exception:
            pass
        return jsonify(ok=True, inserted_id=str(res.inserted_id))
    except Exception as e:
        log.exception("Error insertando autosave")
        return jsonify(error="insert_failed", details=str(e)), 500

@app.get("/autosaves/latest")
@auth_required
def get_latest_autosaves():
    if col_autosaves is None:
        return jsonify(error="mongo_unavailable"), 503
    try:
        limit = int(request.args.get("limit", "5"))
        limit = 1 if limit < 1 else min(limit, 100)
        cur = col_autosaves.find().sort("timestamp", -1).limit(limit)
        items: List[Dict[str, Any]] = []
        for d in cur:
            d["_id"] = str(d["_id"])
            items.append(d)
        return jsonify(ok=True, items=items)
    except Exception as e:
        log.exception("Error consultando autosaves")
        return jsonify(error="query_failed", details=str(e)), 500

# -----------------------------
# Eventos de seguridad
# -----------------------------
@app.post("/events/log")
@auth_required
def log_event():
    if col_sec_logs is None:
        return jsonify(error="mongo_unavailable"), 503
    try:
        body = LogEventIn(**request.get_json(force=True))
    except ValidationError as ve:
        return jsonify(error="validation_error", details=ve.errors()), 400

    doc = {
        "event_type": body.event_type,
        "payload": body.payload or {},
        "ts": datetime.utcnow(),
        # opcional: quién (del token)
        "by": getattr(request, "jwt_claims", {}).get("sub"),
    }
    try:
        res = col_sec_logs.insert_one(doc)
        return jsonify(ok=True, inserted_id=str(res.inserted_id))
    except Exception as e:
        log.exception("Error insertando evento")
        return jsonify(error="insert_failed", details=str(e)), 500

# -----------------------------
# Arranque local (no usado en Docker)
# -----------------------------
if __name__ == "__main__":
    # Útil para pruebas locales: python autosave_guardian/app.py
    app.run(host="0.0.0.0", port=8080, debug=True)
