# backend/services/audit_logger.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from backend.db.mongodb import get_logs_collection
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def log_access(
    user_id: str,
    email: str,
    rol: str,
    endpoint: str,
    method: str,
    status: int,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    tipo: str = "acceso",
    extra: Optional[Dict[str, Any]] = None,
    **kwargs: Any,  # compat: acepta argumentos extra sin romper
) -> None:
    """
    Inserta un log de acceso en MongoDB (colección 'logs').
    - Mantiene compatibilidad con firmas más amplias (kwargs ignorados).
    - Registra info de red si está disponible.
    """
    try:
        doc: Dict[str, Any] = {
            "user_id": str(user_id) if user_id is not None else "",
            "email": email or "",
            "rol": rol or "usuario",
            "endpoint": endpoint or "",
            "method": method or "",
            "status": int(status),
            "timestamp": datetime.utcnow(),
            "tipo": tipo or "acceso",
        }

        # Campos opcionales
        if ip:
            doc["ip"] = ip
        if user_agent:
            doc["user_agent"] = user_agent
        if extra and isinstance(extra, dict):
            # Evita sobreescribir claves críticas
            for k, v in extra.items():
                if k not in doc:
                    doc[k] = v

        get_logs_collection().insert_one(doc)
    except Exception as e:
        # No interrumpir el flujo del negocio por un fallo de logging
        logger.warning(f"[audit_logger] No se pudo registrar log de acceso: {e}")
