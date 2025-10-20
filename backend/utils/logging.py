# backend/utils/logging.py
import logging
import os
from logging.handlers import RotatingFileHandler
from logging import Logger

from backend.config.settings import settings, configure_logging

# Si usas un middleware que expone un request-id, lo integramos;
# si no existe, el filtro retorna vacío y no rompe.
try:
    from backend.middleware.request_id import get_request_id  # ContextVar
except Exception:
    def get_request_id() -> str | None:
        return None


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


def setup_logging(level: int | None = None) -> None:
    """
    Configura el root logger una sola vez:
    - Nivel según DEBUG (o parámetro)
    - Handler a consola (stdout)
    - Handler a archivo rotativo en LOG_DIR/system.log
    - Ambos con RequestIdFilter para rid=...
    - Propaga logs de uvicorn/httpx hacia root con el mismo formato
    """
    # Primero invoca la configuración básica (archivo + consola)
    configure_logging(level=level)

    # Ajusta formato enriquecido y rotación a archivo
    fmt = "%(asctime)s | %(levelname)s | %(name)s | rid=%(request_id)s | %(message)s"
    formatter = logging.Formatter(fmt)
    rid_filter = RequestIdFilter()

    # Asegurar carpeta para logs
    log_dir = getattr(settings, "log_dir", "./logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "system.log")

    # Reemplazar handlers del root con los definitivos
    root = logging.getLogger()
    root.handlers.clear()

    stream_h = logging.StreamHandler()
    stream_h.setFormatter(formatter)
    stream_h.addFilter(rid_filter)
    root.addHandler(stream_h)

    file_h = RotatingFileHandler(log_path, maxBytes=10_000_000, backupCount=5, encoding="utf-8")
    file_h.setFormatter(formatter)
    file_h.addFilter(rid_filter)
    root.addHandler(file_h)

    level_eff = logging.DEBUG if getattr(settings, "debug", False) else logging.INFO
    root.setLevel(level if level is not None else level_eff)

    # Alinear loggers de uvicorn y librerías comunes
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "httpx"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True
        lg.setLevel(root.level)


def get_logger(name: str) -> Logger:
    """Obtén un logger por módulo. No añade handlers (hereda del root)."""
    return logging.getLogger(name)