import subprocess
from datetime import datetime
import os
import shutil

def entrenar_y_loggear():
    # ✅ Validar que Rasa esté instalado
    if not shutil.which("rasa"):
        return {
            "log_path": None,
            "success": False,
            "error": "❌ Rasa CLI no está instalado o no está en el PATH"
        }

    # 📁 Crear carpeta logs si no existe
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    # 🕓 Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    log_path = os.path.join(log_dir, f"train_{timestamp}.log")

    # 🛠️ Comando de entrenamiento
    comando = [
        "rasa", "train",
        "--domain", "rasa/domain.yml",
        "--data", "rasa/data/",
        "--config", "rasa/config.yml"
    ]

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"🔧 Entrenamiento iniciado: {datetime.now()}\n")
        log_file.write(f"📁 Ejecutando comando: {' '.join(comando)}\n\n")

        try:
            subprocess.run(comando, stdout=log_file, stderr=subprocess.STDOUT, check=True)
            log_file.write("\n✅ Entrenamiento finalizado correctamente.\n")
            return {
                "log_path": log_path,
                "success": True,
                "message": "✅ Entrenamiento exitoso"
            }
        except subprocess.CalledProcessError as e:
            log_file.write("\n❌ Error durante el entrenamiento.\n")
            log_file.write(f"🛠️ Código de error: {e.returncode}\n")
            return {
                "log_path": log_path,
                "success": False,
                "error": "❌ Error durante el entrenamiento. Revisa el log."
            }