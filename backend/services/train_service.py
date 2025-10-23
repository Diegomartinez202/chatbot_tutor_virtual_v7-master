# backend/services/train_service.py
from __future__ import annotations

import subprocess
from typing import Dict, Optional

from backend.config.settings import settings
from backend.services.log_service import log_access


def entrenar_chatbot() -> Dict[str, str]:
    """
    Ejecuta el comando de entrenamiento de Rasa definido en settings.
    Retorna un dict con el estado y la salida del proceso.
    No lanza excepciones: encapsula errores y devuelve status apropiado.
    """
    try:
        cmd = (settings.rasa_train_command or "").strip()
        if not cmd:
            return {
                "status": "error",
                "message": "RASA_TRAIN_COMMAND no definido en settings.",
                "error": "missing_command",
            }

        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return {
                "status": "ok",
                "message": "Entrenamiento completado correctamente.",
                "output": result.stdout,
            }

        return {
            "status": "error",
            "message": "Fallo durante el entrenamiento.",
            "error": result.stderr or "unknown_error",
        }

    except Exception as e:
        return {
            "status": "exception",
            "message": "Error inesperado al entrenar.",
            "error": str(e),
        }


def entrenar_y_loggear(user: Optional[Dict] = None) -> Dict[str, str]:
    """
    Llama a entrenar_chatbot y registra el evento en logs.
    El parametro user es opcional y puede contener:
      {_id|id, email, rol, ip, user_agent}
    """
    result = entrenar_chatbot()

    # Status HTTP aproximado para el log
    status_code = 200 if result.get("status") == "ok" else 500

    # Datos del usuario (opcionales)
    user = user or {}
    user_id = user.get("_id") or user.get("id")
    email = user.get("email")
    rol = user.get("rol")
    ip = user.get("ip")
    user_agent = user.get("user_agent")

    # Registrar acceso/accion
    try:
        log_access(
            user_id=user_id if user_id is not None else "",
            email=email if email is not None else "",
            rol=rol if rol is not None else "",
            endpoint="/admin/train",
            method="POST",
            status=status_code,
            ip=ip,
            user_agent=user_agent,
            tipo="accion",
        )
    except Exception:
        # No romper si el log falla
        pass

    return result