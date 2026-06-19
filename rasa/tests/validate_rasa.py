import os
import subprocess
from pathlib import Path
import webbrowser
import time

# ========================
# 🧩 CONFIGURACIÓN INICIAL
# ========================
BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"
REPORT_PATH = RESULTS_DIR / "report.html"

# ========================
# ⚙️ FUNCIONES AUXILIARES
# ========================
def run_command(description, command):
    print(f"\n🔹 {description}\n{'-' * 60}")
    process = subprocess.run(command, shell=True)
    if process.returncode != 0:
        print(f"❌ ERROR en: {description}")
        print("   → Revisa el mensaje anterior para detalles.")
        time.sleep(1)
        return False
    print(f"✅ {description} completado correctamente.")
    return True


def clean_old_results():
    print("\n🧹 Limpiando modelos y resultados anteriores...")
    os.system("rasa stop >nul 2>&1")
    os.system("rmdir /s /q models results __pycache__ >nul 2>&1" if os.name == "nt" else "rm -rf models results __pycache__")
    RESULTS_DIR.mkdir(exist_ok=True)
    print("✅ Limpieza completada.\n")


# ========================
# 🧪 VALIDACIÓN COMPLETA
# ========================
def main():
    print("🚀 Iniciando diagnóstico completo del proyecto Rasa...\n")

    # 1️⃣ Limpieza previa
    clean_old_results()

    # 2️⃣ Validar estructura y dominio
    run_command("Validando estructura del proyecto", "rasa data validate")

    # 3️⃣ Validar dominio
    run_command("Validando dominio (domain.yml)", "rasa data validate domain")

    # 4️⃣ Validar intents, reglas e historias
    run_command("Validando reglas e historias", "rasa data validate stories")
    run_command("Validando reglas (rules)", "rasa data validate rules")

    # 5️⃣ Validar acciones personalizadas
    if Path(BASE_DIR / "actions").exists():
        run_command("Verificando sintaxis de acciones", "python -m py_compile actions/*.py")

    # 6️⃣ Entrenar el modelo
    if not run_command("Entrenando modelo", "rasa train"):
        print("⚠️ Error en entrenamiento — revisa los intents o YAML.")
        return

    # 7️⃣ Ejecutar pruebas automáticas (si existen)
    test_file = BASE_DIR / "data/test_encuesta.yml"
    if test_file.exists():
        run_command("Ejecutando pruebas automáticas", f"rasa test --stories {test_file}")
    else:
        print("⚠️ No se encontró data/test_encuesta.yml. Se omiten pruebas automáticas.")

    # 8️⃣ Ver reporte de resultados
    if REPORT_PATH.exists():
        print(f"\n📊 Abriendo reporte de resultados: {REPORT_PATH}")
        webbrowser.open_new_tab(REPORT_PATH.as_uri())
    else:
        print("\n⚠️ No se generó el reporte HTML. Verifica los logs en /results.")

    print("\n✅ Diagnóstico completado. Revisa los mensajes anteriores para detalles.")


# ========================
# ▶️ EJECUCIÓN PRINCIPAL
# ========================
if __name__ == "__main__":
    main()
