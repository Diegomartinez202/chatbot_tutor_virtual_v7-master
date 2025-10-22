# backend/config/settings.py
from __future__ import annotations

import os
import os.path
import json
import logging
from typing import List, Optional, Literal, Any

from pydantic import Field, EmailStr

# 🔧 Compatibilidad con entornos donde pydantic_settings puede no resolverse correctamente
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # Fallback para evitar error en IDE (sin romper ejecución)
    try:
        import pydantic_settings as _ps
        BaseSettings = getattr(_ps, "BaseSettings")
        SettingsConfigDict = getattr(_ps, "SettingsConfigDict")
    except Exception:
        raise ImportError(
            "⚠️ No se pudo importar 'pydantic_settings'. Ejecuta: pip install pydantic-settings"
        )

# 🔧 Compatibilidad Pydantic v1/v2
try:
    from pydantic import field_validator, model_validator
    _V2 = True
except Exception:
    from pydantic import validator as field_validator  # type: ignore

    def model_validator(*args, **kwargs):  # type: ignore
        def _decor(f):
            return f
        return _decor

    _V2 = False


def _resolve_env_file() -> str:
    """
    Permite usar:
      - ENV_FILE=/ruta/custom.env  (toma prioridad)
      - .env (si existe)
      - .env.<APP_ENV>  (fallback: .env.dev)
    """
    explicit = os.getenv("ENV_FILE")
    if explicit and os.path.exists(explicit):
        return explicit

    if os.path.exists(".env"):
        return ".env"

    app_env = (os.getenv("APP_ENV") or "dev").strip()
    candidate = f".env.{app_env}"
    return candidate

class Settings(BaseSettings):
    demo_mode: bool = True  # 🔧 Activa modo DEMO para la sustentación
    jwt_algorithm: str = "HS256"
    secret_key: str = "TU_CLAVE_SECRETA"

class Settings(BaseSettings):
    """
    Configuración centralizada del proyecto.
    Incluye soporte para JWT (HS y RS), MongoDB, Rasa, SMTP, S3,
    CSP/embebido, rate limiting, helpdesk, etc.
    """

    # === Configuración general ===
    model_config = SettingsConfigDict(
        env_file=_resolve_env_file(),
        case_sensitive=False,
    )
    # === 🔧 MODO DEMO PARA SUSTENTACIÓN ===
    demo_mode: bool = Field(default=True, alias="DEMO_MODE")
    """
    Si demo_mode=True:
      - El backend aceptará el token simulado: Authorization: Bearer FAKE_TOKEN_ZAJUNA
      - Ideal para presentaciones o entornos sin conexión real con Zajuna.
    """

    # ✅ ⚙️ Compatibilidad con Pydantic v1 y v2
    if not _V2:
        class Config:
            pass

    # 📦 MongoDB
    mongo_uri: str = Field(..., alias="MONGO_URI")
    mongo_db_name: str = Field(..., alias="MONGO_DB_NAME")

    # 🔐 JWT (emisión/validación HS* y validación RS*/JWKS)
    secret_key: Optional[str] = Field(default=None, alias="SECRET_KEY")  # HS*
    jwt_public_key: Optional[str] = Field(default=None, alias="JWT_PUBLIC_KEY")  # RS* (PEM)
    jwt_jwks_url: Optional[str] = Field(default=None, alias="JWT_JWKS_URL")      # RS* (JWKS remoto)
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Validaciones extra opcionales para decodificación
    jwt_issuer: Optional[str] = Field(default=None, alias="JWT_ISSUER")
    jwt_audience: Optional[str] = Field(default=None, alias="JWT_AUDIENCE")
    leeway_seconds: Optional[int] = Field(default=None, alias="JWT_LEEWAY_SECONDS")

    # ✅ Compat temporal para tokens sin "typ"
    jwt_accept_typeless: bool = Field(default=False, alias="JWT_ACCEPT_TYPELESS")

    # ✅ Nombre de la cookie de refresh
    refresh_cookie_name: str = Field(default="rt", alias="REFRESH_COOKIE_NAME")

    # 🤖 Rasa Bot
    rasa_url: str = Field(..., alias="RASA_URL")
    rasa_data_path: str = Field(default="rasa/data/nlu.yml", alias="RASA_DATA_PATH")
    rasa_domain_path: str = Field(default="rasa/domain.yml", alias="RASA_DOMAIN_PATH")
    rasa_model_path: str = Field(default="rasa/models", alias="RASA_MODEL_PATH")
    rasa_train_command: str = Field(default="rasa train", alias="RASA_TRAIN_COMMAND")

    # 📧 SMTP
    smtp_server: str = Field(..., alias="SMTP_SERVER")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(..., alias="SMTP_USER")
    smtp_pass: str = Field(..., alias="SMTP_PASS")
    email_from: EmailStr = Field(..., alias="EMAIL_FROM")
    email_to: EmailStr = Field(..., alias="EMAIL_TO")

    # 👤 Admin
    admin_email: EmailStr = Field(..., alias="ADMIN_EMAIL")
    admin_bootstrap_password: Optional[str] = Field(default=None, alias="ADMIN_BOOTSTRAP_PASSWORD")

    # 🧾 Logs y entorno
    debug: bool = Field(default=False, alias="DEBUG")
    log_dir: str = Field(default="logs", alias="LOG_DIR")
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173"], alias="ALLOWED_ORIGINS"
    )

    # 📁 Rutas estáticas
    static_dir: str = Field(default="backend/static", alias="STATIC_DIR")
    template_dir: str = Field(default="backend/templates", alias="TEMPLATE_DIR")
    favicon_path: str = Field(default="backend/static/favicon.ico", alias="FAVICON_PATH")

    # ☁️ S3
    aws_access_key_id: Optional[str] = Field(None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, alias="AWS_SECRET_ACCESS_KEY")
    aws_s3_bucket_name: Optional[str] = Field(None, alias="AWS_S3_BUCKET_NAME")
    aws_s3_region: str = Field(default="us-east-1", alias="AWS_S3_REGION")
    aws_s3_endpoint_url: str = Field(default="https://s3.amazonaws.com", alias="AWS_S3_ENDPOINT_URL")

    # 🌐 URL base de backend
    base_url: str = Field(default="http://localhost:8000", alias="BASE_URL")

    # 🧩 Embebido (CSP + redirects)
    frame_ancestors: List[str] = Field(default_factory=lambda: ["'self'"], alias="FRAME_ANCESTORS")
    embed_enabled: bool = Field(default=True, alias="EMBED_ENABLED")
    frontend_site_url: str = Field(default="http://localhost:5173", alias="FRONTEND_SITE_URL")

    # 🌱 Entorno
    app_env: Literal["dev", "test", "prod"] = Field(default="dev", alias="APP_ENV")

    # 🚦 Rate limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_backend: Literal["memory", "redis"] = Field(default="memory", alias="RATE_LIMIT_BACKEND")
    rate_limit_window_sec: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SEC")
    rate_limit_max_requests: int = Field(default=60, alias="RATE_LIMIT_MAX_REQUESTS")
    redis_url: Optional[str] = Field(None, alias="REDIS_URL")
    rate_limit_storage_uri: Optional[str] = Field(default=None, alias="RATE_LIMIT_STORAGE_URI")
    rate_limit_key_strategy: Literal["user_or_ip", "skip_admin", "ip"] = Field(
        default="user_or_ip", alias="RATE_LIMIT_KEY_STRATEGY"
    )

    # 📞 Helpdesk / Escalada a humano
    helpdesk_kind: Literal["webhook", "zendesk", "freshdesk", "jira", "zoho"] = Field(
        default="webhook", alias="HELPDESK_KIND"
    )
    helpdesk_webhook: Optional[str] = Field(None, alias="HELPDESK_WEBHOOK")
    helpdesk_token: Optional[str] = Field(None, alias="HELPDESK_TOKEN")

    # ─────────────────────────────────────────────────────────────
    # ✅ Campos "compat" para NO ignorar variables extra del .env
    # ─────────────────────────────────────────────────────────────

    # Mongo compat
    mongodb_url: Optional[str] = Field(default=None, alias="MONGODB_URL")
    mongodb_db: Optional[str] = Field(default=None, alias="MONGODB_DB")
    mongo_url: Optional[str] = Field(default=None, alias="MONGO_URL")
    mongo_db: Optional[str] = Field(default=None, alias="MONGO_DB")

    # Rasa compat
    rasa_rest_url: Optional[str] = Field(default=None, alias="RASA_REST_URL")
    rasa_ws_url: Optional[str] = Field(default=None, alias="RASA_WS_URL")

    # Rate limit provider
    rate_limit_provider: Optional[Literal["builtin", "slowapi", "fastapi-limiter"]] = Field(
        default=None, alias="RATE_LIMIT_PROVIDER"
    )

    # CSP/Embed compat
    embed_allowed_origins: Optional[List[str]] = Field(default=None, alias="EMBED_ALLOWED_ORIGINS")

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

    # ─────────────────────────────────────────────────────────────
    # Normalizadores CSV/JSON → lista
    # ─────────────────────────────────────────────────────────────
    @field_validator("allowed_origins", "frame_ancestors", mode="before")
    @classmethod
    def _csv_or_json(cls, v):
        if v is None:
            return v
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("["):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    pass
            return [x.strip() for x in s.split(",") if x.strip()]
        return v

    # Normalizador también para EMBED_ALLOWED_ORIGINS (compat)
    @field_validator("embed_allowed_origins", mode="before")
    @classmethod
    def _csv_or_json_embed(cls, v):
        if v is None:
            return v
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("["):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    pass
            return [x.strip() for x in s.split(",") if x.strip()]
        return v

    # Normalizador de APP_ENV
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
            "staging": "test",
            "prod": "prod",
            "production": "prod",
        }
        return mapping.get(s, s)

    # ─────────────────────────────────────────────────────────────
    # Validaciones condicionales
    # ─────────────────────────────────────────────────────────────
    @model_validator(mode="after")
    def _validate_conditional_requirements(self):
        if (
            self.rate_limit_enabled
            and self.rate_limit_backend == "redis"
            and not (self.rate_limit_storage_uri and str(self.rate_limit_storage_uri).strip())
            and not (self.redis_url and str(self.redis_url).strip())
        ):
            raise ValueError(
                "Se requiere REDIS_URL (o RATE_LIMIT_STORAGE_URI) cuando RATE_LIMIT_BACKEND='redis'"
            )

        alg = (self.jwt_algorithm or "").upper().strip()
        if alg.startswith("RS"):
            # ✅ Ahora aceptamos PUBLIC KEY o JWKS URL
            if not ((self.jwt_public_key and self.jwt_public_key.strip()) or (self.jwt_jwks_url and self.jwt_jwks_url.strip())):
                raise ValueError("Para RS*, define JWT_PUBLIC_KEY (PEM) o JWT_JWKS_URL (JWKS remoto).")
        elif alg.startswith("HS"):
            if not (self.secret_key and self.secret_key.strip()):
                raise ValueError("Se requiere SECRET_KEY cuando JWT_ALGORITHM es HS* (p.ej., HS256)")
        else:
            raise ValueError(f"JWT_ALGORITHM no soportado: {self.jwt_algorithm!r}. Usa HS* o RS*.")

        return self

    # ─────────────────────────────────────────────────────────────
    # Helpers / Compat
    # ─────────────────────────────────────────────────────────────
    @property
    def s3_enabled(self) -> bool:
        return bool(
            self.aws_s3_bucket_name and self.aws_access_key_id and self.aws_secret_access_key
        )

    @property
    def rasa_rest_base(self) -> str:
        return self.rasa_url

    @property
    def allowed_origins_list(self) -> List[str]:
        return list(self.allowed_origins or [])

    def build_csp(self) -> str:
        fa = " ".join(self.frame_ancestors or ["'self'"])
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

    @property
    def jwt_secret(self) -> Optional[str]:
        # Código legacy usa settings.jwt_secret → ahora es secret_key
        return self.secret_key

    @property
    def jwt_expiration_minutes(self) -> int:
        # Código legacy usa settings.jwt_expiration_minutes → ahora es access_token_expire_minutes
        return self.access_token_expire_minutes

    @property
    def jwt_refresh_cookie_name(self) -> str:
        # Por si en algún módulo antiguo se usa este nombre
        return self.refresh_cookie_name


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