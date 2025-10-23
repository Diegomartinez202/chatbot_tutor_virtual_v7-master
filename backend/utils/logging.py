# =====================================================
# 🧩 backend/utils/logging.py
# =====================================================
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from logging import Logger
from typing import Any

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
    def get_request_id() -> str | None:
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
# 🪵 Configuración del Logging
# =====================================================
def setup_logging(level: int | None = None) -> None:
    """
    Configura el logging global del sistema:
    - Consola + archivo rotativo
    - Formato uniforme
    - request_id opcional (si existe)
    - Integración con uvicorn/httpx
    """
    # Invoca configuración base (si existe)
    try:
        configure_logging(level=level)
    except Exception:
        pass

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | rid=%(request_id)s | %(message)s"
    formatter = logging.Formatter(fmt)
    rid_filter = RequestIdFilter()

    # 🧩 Asegurar carpeta de logs con coerción robusta
    raw_dir = getattr(settings, "log_dir", "./logs")
    log_dir = _coerce_log_dir(raw_dir, "./logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "system.log")

    # Limpiar handlers previos del root
    root = logging.getLogger()
    root.handlers.clear()

    # Handler consola
    stream_h = logging.StreamHandler()
    stream_h.setFormatter(formatter)
    stream_h.addFilter(rid_filter)
    root.addHandler(stream_h)

    # Handler archivo rotativo
    file_h = RotatingFileHandler(
        log_path,
        maxBytes=10_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_h.setFormatter(formatter)
    file_h.addFilter(rid_filter)
    root.addHandler(file_h)

    # Nivel efectivo
    level_eff = logging.DEBUG if getattr(settings, "debug", False) else logging.INFO
    root.setLevel(level if level is not None else level_eff)

    # Alinear loggers comunes
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "httpx"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True
        lg.setLevel(root.level)

    root.info("✅ Logging inicializado correctamente (directorio: %s)", log_dir)


# =====================================================
# 🔎 Acceso a logger de módulo
# =====================================================
def get_logger(name: str) -> Logger:
    """Obtiene un logger de módulo (hereda formato del root)."""
    return logging.getLogger(name)