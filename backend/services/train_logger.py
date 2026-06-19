# =====================================================
# 🧩 backend/services/train_logger.py
# =====================================================
from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime

from backend.config.settings import settings  # opcional, para rutas si existen


def _logs_dir() -> str:
    """
    Usa settings.log_dir si está definido; de lo contrario ./logs.
    """
    try:
        log_dir = getattr(settings, "log_dir", None)
        if isinstance(log_dir, str) and log_dir.strip():
            return log_dir.strip()
    except Exception:
        pass
    return os.path.join(os.getcwd(), "logs")


def entrenar_y_loggear():
    """
    Ejecuta `rasa train` y guarda toda la salida en un archivo de logs con timestamp.
    Mantiene exactamente el comportamiento original, añadiendo:
      - uso de settings.log_dir si existe
      - mensajes claros y estructura de retorno consistente
    """
    # ✅ Validar que Rasa esté instalado
    if not shutil.which("rasa"):
        return {
            "log_path": None,
            "success": False,
            "error": "❌ Rasa CLI no está instalado o no está en el PATH",
        }

    # 📁 Crear carpeta logs si no existe
    log_dir = _logs_dir()
    os.makedirs(log_dir, exist_ok=True)

    # 🕓 Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    log_path = os.path.join(log_dir, f"train_{timestamp}.log")

    # 🛠️ Comando de entrenamiento (mantenemos el original)
    comando = [
        "rasa",
        "train",
        "--domain",
        "rasa/domain.yml",
        "--data",
        "rasa/data/",
        "--config",
        "rasa/config.yml",
    ]

    # 📝 Ejecutar y volcar salida al log
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"🔧 Entrenamiento iniciado: {datetime.now()}\n")
        log_file.write(f"📁 Ejecutando comando: {' '.join(comando)}\n\n")

        try:
            subprocess.run(comando, stdout=log_file, stderr=subprocess.STDOUT, check=True)
            log_file.write("\n✅ Entrenamiento finalizado correctamente.\n")
            return {
                "log_path": log_path,
                "success": True,
                "message": "✅ Entrenamiento exitoso",
            }
        except subprocess.CalledProcessError as e:
            log_file.write("\n❌ Error durante el entrenamiento.\n")
            log_file.write(f"🛠️ Código de error: {e.returncode}\n")
            return {
                "log_path": log_path,
                "success": False,
                "error": "❌ Error durante el entrenamiento. Revisa el log.",
            }
        except Exception as e:
            log_file.write("\n❌ Excepción inesperada durante el entrenamiento.\n")
            log_file.write(f"🧯 Detalle: {e}\n")
            return {
                "log_path": log_path,
                "success": False,
                "error": f"❌ Excepción inesperada: {e}",
            }