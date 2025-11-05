# backend/config/settings.py
from __future__ import annotations

import os
import os.path
import json
import logging
from typing import List, Optional, Literal, Any, Dict, Union

from pydantic import Field, EmailStr

# 🔧 Compat pydantic_settings
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # Fallback IDE
    try:
        import pydantic_settings as _ps  # type: ignore
        BaseSettings = getattr(_ps, "BaseSettings")  # type: ignore
        SettingsConfigDict = getattr(_ps, "SettingsConfigDict")  # type: ignore
    except Exception:
        raise ImportError(
            "⚠️ No se pudo importar 'pydantic_settings'. Ejecuta: pip install pydantic-settings"
        )

# 🔧 Compat Pydantic v1/v2
try:
    from pydantic import field_validator, model_validator  # type: ignore
    _V2 = True
except Exception:
    from pydantic import validator as field_validator  # type: ignore

    def model_validator(*_args, **_kwargs):  # type: ignore
        def _decor(f):
            return f
        return _decor

    _V2 = False


def _resolve_env_file() -> str:
    """
    Orden de resolución:
      - ENV_FILE=/ruta/custom.env
      - .env
      - .env.<APP_ENV> (fallback dev)
    """
    explicit = os.getenv("ENV_FILE")
    if explicit and os.path.exists(explicit):
        return explicit
    if os.path.exists(".env"):
        return ".env"
    app_env = (os.getenv("APP_ENV") or "dev").strip()
    return f".env.{app_env}"


JsonOrCsv = Union[str, List[str]]


class Settings(BaseSettings):
    """
    Configuración centralizada del proyecto.
    Incluye soporte para JWT (HS/RS), MongoDB, Rasa, SMTP, S3,
    CSP/embebido, rate limiting, helpdesk, etc.
    """

    # === Configuración general (Pydantic v2) ===
    if _V2:
        model_config = SettingsConfigDict(
            env_file=_resolve_env_file(),
            case_sensitive=False,
            extra="ignore",  # ✅ ignora envs no mapeados (e.g., NODE_ENV)
        )

    # 🌱 Entorno
    app_env: Literal["dev", "test", "prod", "staging"] = Field(default="dev", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    demo_mode: bool = Field(default=True, alias="DEMO_MODE")
    base_url: str = Field(default="http://localhost:8000", alias="BASE_URL")

    # 📦 MongoDB (todas las variantes por compat)
    mongo_uri: Optional[str] = Field(default=None, alias="MONGO_URI")
    mongo_db_name: Optional[str] = Field(default=None, alias="MONGO_DB_NAME")
    mongodb_url: Optional[str] = Field(default=None, alias="MONGODB_URL")
    mongodb_db: Optional[str] = Field(default=None, alias="MONGODB_DB")
    mongo_url: Optional[str] = Field(default=None, alias="MONGO_URL")
    mongo_db: Optional[str] = Field(default=None, alias="MONGO_DB")

    # 🔐 JWT (HS* y compat RS*)
    secret_key: Optional[str] = Field(default=None, alias="SECRET_KEY")  # HS*
    jwt_public_key: Optional[str] = Field(default=None, alias="JWT_PUBLIC_KEY")  # RS* (PEM)
    jwt_jwks_url: Optional[str] = Field(default=None, alias="JWT_JWKS_URL")      # RS* (JWKS remoto)
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Validaciones extra opcionales para decodificación
    jwt_issuer: Optional[str] = Field(default=None, alias="JWT_ISSUER")
    jwt_audience: Optional[str] = Field(default=None, alias="JWT_AUDIENCE")
    jwt_leeway_seconds: int = Field(default=0, alias="JWT_LEEWAY_SECONDS")
    jwt_accept_typeless: bool = Field(default=True, alias="JWT_ACCEPT_TYPELESS")

    # ⏳ Refresh cookie (nombre configurable)
    refresh_cookie_name: str = Field(default="rt", alias="REFRESH_COOKIE_NAME")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # 🤖 Rasa Bot (y compat)
    rasa_url: str = Field(default="http://localhost:5005", alias="RASA_URL")
    rasa_rest_url: Optional[str] = Field(default=None, alias="RASA_REST_URL")
    rasa_ws_url: Optional[str] = Field(default=None, alias="RASA_WS_URL")

    rasa_data_path: str = Field(default="rasa/data/nlu.yml", alias="RASA_DATA_PATH")
    rasa_domain_path: str = Field(default="rasa/domain.yml", alias="RASA_DOMAIN_PATH")
    rasa_model_path: str = Field(default="rasa/models", alias="RASA_MODEL_PATH")
    rasa_train_command: str = Field(default="rasa train", alias="RASA_TRAIN_COMMAND")

    # 📧 SMTP
    smtp_server: str = Field(default="localhost", alias="SMTP_SERVER")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="demo@example.com", alias="SMTP_USER")
    smtp_pass: str = Field(default="demo", alias="SMTP_PASS")
    email_from: EmailStr = Field(default="demo@example.com", alias="EMAIL_FROM")
    email_to: EmailStr = Field(default="admin@example.com", alias="EMAIL_TO")

    # 👤 Admin bootstrap opcional
    admin_email: EmailStr = Field(default="admin@example.com", alias="ADMIN_EMAIL")
    admin_bootstrap_password: Optional[str] = Field(default=None, alias="ADMIN_BOOTSTRAP_PASSWORD")

    # 🧾 Logs y rutas
    log_dir: str = Field(default="logs", alias="LOG_DIR")
    static_dir: str = Field(default="backend/static", alias="STATIC_DIR")
    template_dir: str = Field(default="backend/templates", alias="TEMPLATE_DIR")
    favicon_path: str = Field(default="backend/static/favicon.ico", alias="FAVICON_PATH")

    # 🌐 CORS/EMBED/CSP (aceptamos JSON o CSV en .env)
    allowed_origins: JsonOrCsv = Field(default='["http://localhost:5173"]', alias="ALLOWED_ORIGINS")
    embed_allowed_origins: JsonOrCsv = Field(
        default='["\'self\'","http://localhost:5173","http://localhost:8080"]',
        alias="EMBED_ALLOWED_ORIGINS",
    )
    frame_ancestors: JsonOrCsv = Field(default="['self']", alias="FRAME_ANCESTORS")
    frontend_site_url: str = Field(default="http://localhost:5173", alias="FRONTEND_SITE_URL")
    embed_enabled: bool = Field(default=True, alias="EMBED_ENABLED")
    allow_registration: bool = Field(default=True, alias="ALLOW_REGISTRATION")
    chat_require_auth: bool = Field(default=False, alias="CHAT_REQUIRE_AUTH")
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")

    # ☁️ S3
    aws_access_key_id: Optional[str] = Field(None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, alias="AWS_SECRET_ACCESS_KEY")
    aws_s3_bucket_name: Optional[str] = Field(None, alias="AWS_S3_BUCKET_NAME")
    aws_s3_region: str = Field(default="us-east-1", alias="AWS_S3_REGION")
    aws_s3_endpoint_url: str = Field(default="https://s3.amazonaws.com", alias="AWS_S3_ENDPOINT_URL")

    # 🚦 Rate limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_backend: Literal["memory", "redis"] = Field(default="memory", alias="RATE_LIMIT_BACKEND")
    rate_limit_window_sec: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SEC")
    rate_limit_max_requests: int = Field(default=60, alias="RATE_LIMIT_MAX_REQUESTS")
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    rate_limit_storage_uri: Optional[str] = Field(default=None, alias="RATE_LIMIT_STORAGE_URI")
    rate_limit_key_strategy: Literal["user_or_ip", "skip_admin", "ip"] = Field(
        default="user_or_ip", alias="RATE_LIMIT_KEY_STRATEGY"
    )
    rate_limit_provider: Optional[Literal["builtin", "slowapi", "fastapi-limiter"]] = Field(
        default=None, alias="RATE_LIMIT_PROVIDER"
    )

    # 📞 Helpdesk / Escalada a humano
    helpdesk_kind: Literal["webhook", "zendesk", "freshdesk", "jira", "zoho"] = Field(
        default="webhook", alias="HELPDESK_KIND"
    )
    helpdesk_webhook: Optional[str] = Field(None, alias="HELPDESK_WEBHOOK")
    helpdesk_token: Optional[str] = Field(None, alias="HELPDESK_TOKEN")

    # Rasa tracker compat
    action_server_url: Optional[str] = Field(default=None, alias="ACTION_SERVER_URL")
    tracker_mongo_url: Optional[str] = Field(default=None, alias="TRACKER_MONGO_URL")
    tracker_mongo_db: Optional[str] = Field(default=None, alias="TRACKER_MONGO_DB")
    tracker_mongo_collection: Optional[str] = Field(default=None, alias="TRACKER_MONGO_COLLECTION")

    # RabbitMQ compat
    rabbitmq_url: Optional[str] = Field(default=None, alias="RABBITMQ_URL")
    rabbitmq_user: Optional[str] = Field(default=None, alias="RABBITMQ_USER")
    rabbitmq_password: Optional[str] = Field(default=None, alias="RABBITMQ_PASSWORD")

    # Docker compose profiles compat
    compose_profiles: Optional[str] = Field(default=None, alias="COMPOSE_PROFILES")

    # --- Sinks de compatibilidad (evitan errores por "extra") ---
    node_env: Optional[str] = Field(default=None, alias="NODE_ENV")
    environment_compat: Optional[str] = Field(default=None, alias="ENVIRONMENT")

    # 🆕 Política explícita (opcional) para Permissions-Policy.
    permissions_policy: Optional[str] = Field(
        default_factory=lambda: os.getenv("PERMISSIONS_POLICY") or None
    )

    # ───────────────────────────────
    # Validadores/normalizadores
    # ───────────────────────────────
    @field_validator("app_env", mode="before")
    @classmethod
    def _coerce_app_env(cls, v: Any) -> str:
        if v is None:
            return "dev"
        s = str(v).strip().lower()
        mapping = {
            "development": "dev",
            "develop": "dev",
            "dev": "dev",
            "testing": "test",
            "test": "test",
            "staging": "staging",
            "prod": "prod",
            "production": "prod",
        }
        return mapping.get(s, s)

    @staticmethod
    def _parse_json_or_csv(v: JsonOrCsv, default: List[str]) -> List[str]:
        if v is None:
            return list(default)
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return list(default)
            # soporta JSON
            if s.startswith("["):
                try:
                    arr = json.loads(s)
                    if isinstance(arr, list):
                        return [str(x).strip() for x in arr if str(x).strip()]
                except Exception:
                    pass
            # soporta CSV
            return [x.strip() for x in s.split(",") if x.strip()]
        return list(default)

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _norm_allowed_origins(cls, v):
        return cls._parse_json_or_csv(v, default=["http://localhost:5173"])

    @field_validator("embed_allowed_origins", mode="before")
    @classmethod
    def _norm_embed_allowed_origins(cls, v):
        return cls._parse_json_or_csv(v, default=["'self'", "http://localhost:5173", "http://localhost:8080"])

    @field_validator("frame_ancestors", mode="before")
    @classmethod
    def _norm_frame_ancestors(cls, v):
        fa = cls._parse_json_or_csv(v, default=["'self'"])
        # normaliza self => 'self'
        out = []
        for x in fa:
            s = x.strip()
            out.append("'self'" if s.lower() == "self" else s)
        return out

    @model_validator(mode="after")
    def _validate_conditional_requirements(self):
        # Redis requerido si backend=redis
        if (
            self.rate_limit_enabled
            and self.rate_limit_backend == "redis"
            and not (self.rate_limit_storage_uri and str(self.rate_limit_storage_uri).strip())
            and not (self.redis_url and str(self.redis_url).strip())
        ):
            raise ValueError(
                "Se requiere REDIS_URL (o RATE_LIMIT_STORAGE_URI) cuando RATE_LIMIT_BACKEND='redis'"
            )

        # JWT coherente (HS o RS + clave/jwks)
        alg = (self.jwt_algorithm or "").upper().strip()
        if alg.startswith("RS"):
            if not (
                (self.jwt_public_key and self.jwt_public_key.strip())
                or (self.jwt_jwks_url and self.jwt_jwks_url.strip())
            ):
                raise ValueError("Para RS*, define JWT_PUBLIC_KEY o JWT_JWKS_URL.")
        elif alg.startswith("HS"):
            if not (self.secret_key and self.secret_key.strip()):
                raise ValueError("Se requiere SECRET_KEY cuando JWT_ALGORITHM es HS*")
        else:
            raise ValueError(f"JWT_ALGORITHM no soportado: {self.jwt_algorithm!r}")

        return self

    # ───────────────────────────────
    # Helpers
    # ───────────────────────────────
    @property
    def s3_enabled(self) -> bool:
        return bool(
            self.aws_s3_bucket_name and self.aws_access_key_id and self.aws_secret_access_key
        )

    @property
    def rasa_rest_base(self) -> str:
        # Si definiste RASA_REST_URL explícito, úsalo; si no, base en RASA_URL
        return self.rasa_rest_url or self.rasa_url

    @property
    def allowed_origins_list(self) -> List[str]:
        merged, seen = [], set()
        for lst in (self.allowed_origins or []), (self.embed_allowed_origins or []):
            for o in lst:
                s = (o or "").strip()
                if s and s not in seen:
                    merged.append(s)
                    seen.add(s)
        return merged

    def build_csp(self) -> str:
        merged_fa, seen = [], set()
        for lst in (self.frame_ancestors or []), (self.embed_allowed_origins or []):
            for o in lst:
                s = (o or "").strip()
                if s and s not in seen:
                    merged_fa.append(s)
                    seen.add(s)
        fa = " ".join(merged_fa or ["'self'"])
        return (
            "default-src 'self'; "
            f"frame-ancestors {fa}; "
            "img-src 'self' data: blob:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-eval'; "
            "connect-src 'self' *; "
            "frame-src 'self' *; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self' *;"
        )

    @property
    def rate_limit_storage_uri_effective(self) -> str:
        if self.rate_limit_storage_uri and str(self.rate_limit_storage_uri).strip():
            return str(self.rate_limit_storage_uri).strip()
        if self.rate_limit_backend == "redis" and self.redis_url and str(self.redis_url).strip():
            return str(self.redis_url).strip()
        return "memory://"

    # 🔹 Mongo efectivo (con todas tus variantes .env)
    @property
    def mongo_uri_effective(self) -> str:
        """
        Prioridad:
          1) MONGO_URI
          2) MONGO_URL / MONGODB_URL (+ DB si viene aparte)
        Siempre debe ser 'mongodb://host:port[/db]' (NUNCA http://).
        """
        # 1) Si viene MONGO_URI completo, úsalo
        if self.mongo_uri and self.mongo_uri.strip():
            return self.mongo_uri.strip()

        # 2) Armar desde MONGO_URL/MONGODB_URL + DB
        candidate = None
        dbname = (
            self.mongo_db_name
            or self.mongo_db
            or self.mongodb_db
            or "tutor_virtual"
        )

        for k in (self.mongo_url, self.mongodb_url):
            if k and k.strip():
                candidate = k.strip()
                break

        if candidate:
            if "/" in candidate and candidate.rsplit("/", 1)[-1] == dbname:
                return candidate
            # anexar DB si no está
            return candidate.rstrip("/") + f"/{dbname}"

        # 3) Fallback razonable local
        return f"mongodb://localhost:27017/{dbname}"

    @property
    def mongo_db_name_effective(self) -> str:
        return (
            self.mongo_db_name
            or self.mongo_db
            or self.mongodb_db
            or "tutor_virtual"
        )

    @property
    def jwt_secret(self) -> Optional[str]:
        return self.secret_key

    @property
    def jwt_expiration_minutes(self) -> int:
        return self.access_token_expire_minutes

    @property
    def jwt_refresh_cookie_name(self) -> str:
        return self.refresh_cookie_name

    # ─────────────────────────────────────────────────────────
    # Helpers “inteligentes”
    # ─────────────────────────────────────────────────────────
    @property
    def app_env_effective(self) -> str:
        """
        Entorno efectivo en minúsculas (dev/prod/staging/test).
        """
        val = (self.app_env or "prod").lower().strip()
        return val if val in {"dev", "prod", "staging", "test"} else "prod"

    @property
    def permissions_policy_effective(self) -> str:
        """
        Devuelve la Permissions-Policy final:
        - Si PERMISSIONS_POLICY está seteado -> usar literal
        - Si no, preset por entorno:
            dev     -> relajado (autorizamos pruebas locales)
            otro    -> estricto (silencia warnings)
        """
        if self.permissions_policy and str(self.permissions_policy).strip():
            return str(self.permissions_policy).strip()

        if self.app_env_effective == "dev":
            # relaxed
            return "autoplay=(self), clipboard-write=(self), microphone=(self), camera=(self)"
        # strict por defecto
        return "autoplay=(), clipboard-write=(), microphone=(), camera=()"

    # 🔁 Compat Pydantic v1: solo si NO estamos en v2
    if not _V2:
        class Config:
            env_file = _resolve_env_file()
            case_sensitive = False


# Instancia global
settings = Settings()


# ─────────────────────────────────────────────────────────────
# Logging centralizado (helper)
# ─────────────────────────────────────────────────────────────
def configure_logging(level: Optional[int] = None) -> None:
    os.makedirs(settings.log_dir, exist_ok=True)
    log_level = level if level is not None else (logging.DEBUG if settings.debug else logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(settings.log_dir, "app.log"), encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


LOG_DIR = settings.log_dir
