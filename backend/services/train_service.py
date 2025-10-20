import subprocess
from backend.settings import settings  # ✅ Configuración centralizada

def entrenar_chatbot():
    """
    Ejecuta el comando de entrenamiento de Rasa definido en settings.
    Devuelve un diccionario con el estado y salida del proceso.
    """
    try:
        print("🚀 Entrenando chatbot con Rasa...")

        result = subprocess.run(
            settings.rasa_train_command.split(),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✅ Entrenamiento exitoso.")
            return {
                "status": "ok",
                "message": "Entrenamiento completado correctamente.",
                "output": result.stdout
            }
        else:
            print("❌ Error durante entrenamiento.")
            return {
                "status": "error",
                "message": "Fallo durante el entrenamiento.",
                "error": result.stderr
            }

    except Exception as e:
        print(f"❌ Excepción al entrenar: {e}")
        return {
            "status": "exception",
            "message": "Error inesperado al entrenar.",
            "error": str(e)
        }