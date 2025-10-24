# =====================================================
# 🧩 backend/services/message_logger.py
# =====================================================
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

# 📦 Acceso a DB resiliente (evita fallar en import-time)
try:
    from backend.db.mongodb import get_database
except Exception:  # fallback ultra defensivo si el módulo aún no carga
    get_database = None  # type: ignore


def _messages_collection():
    """
    Obtiene la colección 'messages' desde la DB en el momento de uso para
    evitar errores de importación temprana.
    """
    if get_database is None:
        raise RuntimeError("MongoDB aún no está inicializado (get_database no disponible).")
    db = get_database()
    return _get_db()["messages"]


def log_message(user_id: str, text: str, sender: str, extra: Optional[Dict[str, Any]] = None) -> None:
    """
    Inserta un mensaje en la colección 'messages'.
    Mantiene firma original y agrega 'extra' opcional sin romper llamadas existentes.
    """
    doc: Dict[str, Any] = {
        "user_id": str(user_id),
        "text": text,
        "sender": sender,
        "timestamp": datetime.now(timezone.utc),
    }
    if isinstance(extra, dict):
        doc.update(extra)

    try:
        _messages_collection().insert_one(doc)
    except Exception:
        # No romper el flujo por problemas de registro
        # (puedes cambiar por logging si prefieres)
        pass
