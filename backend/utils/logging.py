# backend/utils/logging.py
import logging
import os
from logging.handlers import RotatingFileHandler
from logging import Logger

# Intentamos importar configuración dinámica y variables globales
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


# Intentamos importar request_id si existe middleware
try:
    from backend.middleware.request_id import get_request_id  # ContextVar
except Exception:
    def get_request_id() -> str | None:
        """Retorna el request_id actual o '-' si no hay contexto"""
        return None


class RequestIdFilter(logging.Filter):
    """Agrega el request_id al registro de log"""
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


def setup_logging(level: int | None = None) -> None:
    """
    Configura el logging global del sistema:
    - Consola + archivo rotativo
    - Formato uniforme
    - request_id opcional (si existe)
    - Integración con uvicorn/httpx
    """
    # Invoca configuración base
    try:
        configure_logging(level=level)
    except Exception:
        pass

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | rid=%(request_id)s | %(message)s"
    formatter = logging.Formatter(fmt)
    rid_filter = RequestIdFilter()

    # Asegurar carpeta
    log_dir = getattr(settings, "log_dir", "./logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "system.log")

    root = logging.getLogger()
    root.handlers.clear()

    # Handler consola
    stream_h = logging.StreamHandler()
    stream_h.setFormatter(formatter)
    stream_h.addFilter(rid_filter)
    root.addHandler(stream_h)

    # Handler archivo rotativo
    file_h = RotatingFileHandler(log_path, maxBytes=10_000_000, backupCount=5, encoding="utf-8")
    file_h.setFormatter(formatter)
    file_h.addFilter(rid_filter)
    root.addHandler(file_h)

    # Nivel efectivo
    level_eff = logging.DEBUG if getattr(settings, "debug", False) else logging.INFO
    root.setLevel(level if level is not None else level_eff)

    # Alinear loggers de librerías comunes
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "httpx"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True
        lg.setLevel(root.level)

    root.info("✅ Logging inicializado correctamente")


def get_logger(name: str) -> Logger:
    """Obtiene un logger de módulo (hereda formato del root)."""
    return logging.getLogger(name)