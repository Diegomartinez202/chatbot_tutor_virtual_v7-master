# =====================================================
# 🧩 backend/utils/logging.py
# =====================================================

from __future__ import annotations

import logging
import os
import json
import time
from pathlib import Path
from logging.handlers import RotatingFileHandler
from logging import Logger
from typing import Any, Optional

# =====================================================
# ⚙️ Configuración dinámica y settings
# =====================================================
try:
    from backend.config.settings import settings, configure_logging
except Exception:
    # Fallback mínimo si settings aún no está disponible
    class DummySettings:
        debug = True
        log_dir = "./logs"
    settings = DummySettings()

    def configure_logging(level=None):
        pass


# =====================================================
# 🧩 Middleware opcional: Request ID
# =====================================================
try:
    from backend.middleware.request_id import get_request_id  # ContextVar
except Exception:
    def get_request_id() -> str | None:  # py310+
        """Retorna el request_id actual o '-' si no hay contexto"""
        return None


# =====================================================
# 🔐 Filtro para request_id
# =====================================================
class RequestIdFilter(logging.Filter):
    """Agrega el request_id al registro de log"""
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


# =====================================================
# 🕒 Formateadores (UTC + JSON opcional)
# =====================================================
class UTCFormatter(logging.Formatter):
    converter = time.gmtime  # timestamps en UTC


class JSONFormatter(logging.Formatter):
    converter = time.gmtime
    def format(self, record: logging.LogRecord) -> str:
        base = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", self.converter(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "rid": getattr(record, "request_id", "-"),
            "msg": record.getMessage(),
        }
        # Campos útiles estándar
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)


# =====================================================
# 🧱 Función robusta para coercer log_dir
# =====================================================
def _coerce_log_dir(value: Any, fallback: str = "./logs") -> str:
    """
    Convierte log_dir en str tolerando:
      - str, Path
      - FieldInfo (Pydantic v1/v2)
      - None u otros tipos
    """
    if isinstance(value, (str, Path)):
        return str(value)

    try:
        # Pydantic v2
        from pydantic.fields import FieldInfo as V2FieldInfo  # type: ignore
    except Exception:
        V2FieldInfo = None  # type: ignore

    try:
        # Pydantic v1
        from pydantic.fields import ModelField as V1ModelField  # type: ignore
    except Exception:
        V1ModelField = None  # type: ignore

    if V2FieldInfo and isinstance(value, V2FieldInfo):
        # FieldInfo de Pydantic v2 tiene atributo default
        return str(getattr(value, "default", fallback) or fallback)

    if V1ModelField and isinstance(value, V1ModelField):
        default_val = getattr(value, "default", None)
        if default_val is not None:
            return str(default_val)
        factory = getattr(value, "default_factory", None)
        if callable(factory):
            try:
                return str(factory())
            except Exception:
                pass
        return fallback

    return fallback


# =====================================================
# 🪵 Configuración del Logging (idempotente)
# =====================================================
_CONFIGURED = False  # evita duplicar handlers

def _resolve_level(default_debug: bool) -> int:
    env = (os.getenv("LOG_LEVEL") or "").strip().upper()
    mapping = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARN": logging.WARNING,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }
    if env in mapping:
        return mapping[env]
    return logging.DEBUG if default_debug else logging.INFO


def setup_logging(level: Optional[int] = None, force: bool = False) -> None:
    """
    Configura el logging global del sistema:
    - Consola + archivo rotativo
    - Formato uniforme (texto/JSON)
    - request_id opcional (si existe)
    - Integración con uvicorn/httpx
    - Idempotente (no duplica handlers)
    """
    global _CONFIGURED
    if _CONFIGURED and not force:
        # Ya configurado; no duplicar handlers
        return

    # Invoca configuración base (si existe)
    try:
        configure_logging(level=level)
    except Exception:
        pass

    # ── Formato/Parámetros desde ENV ─────────────────────────
    log_format = (os.getenv("LOG_FORMAT") or "text").strip().lower()  # "text" | "json"
    max_bytes = int(os.getenv("LOG_MAX_BYTES") or "10000000")         # 10MB
    backups   = int(os.getenv("LOG_BACKUPS") or "5")

    # ── Formatters ───────────────────────────────────────────
    text_fmt = "%(asctime)s | %(levelname)-8s | %(name)s | rid=%(request_id)s | %(message)s"
    formatter_text = UTCFormatter(text_fmt)
    formatter_json = JSONFormatter()
    rid_filter = RequestIdFilter()

    # 🧩 Asegurar carpeta de logs con coerción robusta
    raw_dir = getattr(settings, "log_dir", "./logs")
    log_dir = _coerce_log_dir(raw_dir, "./logs")
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        # Si falla crear carpeta, seguimos sólo con consola
        log_dir = None

    log_path = os.path.join(log_dir, "system.log") if log_dir else None

    # Root logger
    root = logging.getLogger()
    root.handlers.clear()

    # Handler consola
    stream_h = logging.StreamHandler()
    stream_h.setFormatter(formatter_json if log_format == "json" else formatter_text)
    stream_h.addFilter(rid_filter)
    root.addHandler(stream_h)

    # Handler archivo rotativo (si posible)
    if log_path:
        try:
            file_h = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backups,
                encoding="utf-8",
            )
            file_h.setFormatter(formatter_json if log_format == "json" else formatter_text)
            file_h.addFilter(rid_filter)
            root.addHandler(file_h)
        except Exception:
            # No bloquear arranque por problemas de filesystem
            pass

    # Nivel efectivo
    level_eff = _resolve_level(getattr(settings, "debug", False))
    root.setLevel(level if level is not None else level_eff)

    # Alinear loggers comunes sin duplicar
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "httpx"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True  # que usen el root
        lg.setLevel(root.level)

    root.info("✅ Logging inicializado correctamente (formato=%s, dir=%s)", log_format, (log_dir or "stdout-only"))
    _CONFIGURED = True


# =====================================================
# 🔎 Acceso a logger de módulo
# =====================================================
def get_logger(name: str) -> Logger:
    """Obtiene un logger de módulo (hereda formato del root)."""
    return logging.getLogger(name)


# =====================================================
# 🔧 Utilidades extra
# =====================================================
def set_global_log_level(level_name: str) -> None:
    """
    Cambia el nivel global en caliente.
    level_name: DEBUG | INFO | WARNING | ERROR | CRITICAL
    """
    lvl = getattr(logging, level_name.upper(), None)
    if not isinstance(lvl, int):
        raise ValueError(f"Nivel inválido: {level_name}")
    logging.getLogger().setLevel(lvl)
    for n in ("uvicorn", "uvicorn.error", "uvicorn.access", "httpx"):
        logging.getLogger(n).setLevel(lvl)
