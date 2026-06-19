import os
import subprocess
import time
import webbrowser
from pathlib import Path

# ========================
# 🧩 CONFIGURACIÓN
# ========================
BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"
REPORT_PATH = RESULTS_DIR / "report.html"

# Colores de consola ANSI
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# ========================
# 🧠 FUNCIONES AUXILIARES
# ========================
def run_command(description, command):
    print(f"\n{CYAN}🔹 {description}{RESET}")
    print("-" * 60)
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"{RED}❌ ERROR en: {description}{RESET}")
        return False
    print(f"{GREEN}✅ {description} completado correctamente.{RESET}")
    return True


def clean_old_results():
    print(f"\n{YELLOW}🧹 Limpiando modelos y resultados anteriores...{RESET}")
    os.system("rasa stop >nul 2>&1")
    os.system("rmdir /s /q models results __pycache__ >nul 2>&1" if os.name == "nt" else "rm -rf models results __pycache__")
    RESULTS_DIR.mkdir(exist_ok=True)
    print(f"{GREEN}✅ Limpieza completada.{RESET}\n")


# ========================
# 🚀 VALIDACIÓN COMPLETA
# ========================
def main():
    print(f"{CYAN}\n🚀 INICIO DEL DIAGNÓSTICO COMPLETO RASA{RESET}")
    print("=" * 60)

    clean_old_results()

    summary = []

    # Validaciones
    steps = [
        ("Validando estructura del proyecto", "rasa data validate"),
        ("Validando dominio (domain.yml)", "rasa data validate domain"),
        ("Validando historias", "rasa data validate stories"),
        ("Validando reglas", "rasa data validate rules"),
    ]

    for desc, cmd in steps:
        ok = run_command(desc, cmd)
        summary.append((desc, ok))

    # Validar acciones personalizadas
    if Path(BASE_DIR / "actions").exists():
        ok = run_command("Verificando sintaxis de acciones", "python -m py_compile actions/*.py")
        summary.append(("Verificación de acciones", ok))

    # Entrenar modelo
    ok = run_command("Entrenando modelo", "rasa train")
    summary.append(("Entrenamiento del modelo", ok))

    # Ejecutar tests
    test_file = BASE_DIR / "data/test_encuesta.yml"
    if test_file.exists():
        ok = run_command("Ejecutando pruebas automáticas", f"rasa test --stories {test_file}")
        summary.append(("Ejecución de pruebas automáticas", ok))
    else:
        print(f"{YELLOW}⚠️ No se encontró {test_file}. Se omiten pruebas automáticas.{RESET}")

    # Mostrar resumen
    print(f"\n{CYAN}📊 RESUMEN FINAL{RESET}")
    print("-" * 60)
    total_ok = 0
    for desc, ok in summary:
        status = f"{GREEN}✔ OK{RESET}" if ok else f"{RED}✖ ERROR{RESET}"
        print(f"{desc:<40} {status}")
        if ok:
            total_ok += 1

    total = len(summary)
    print("-" * 60)
    if total_ok == total:
        print(f"{GREEN}🎉 Todo correcto: {total_ok}/{total} pasos completados exitosamente.{RESET}")
    else:
        print(f"{RED}⚠️ Se detectaron {total - total_ok} errores. Revisa el log anterior.{RESET}")

    # Abrir reporte
    if REPORT_PATH.exists():
        print(f"{CYAN}\n📂 Abriendo reporte: {REPORT_PATH}{RESET}")
        webbrowser.open_new_tab(REPORT_PATH.as_uri())
    else:
        print(f"{YELLOW}\n⚠️ No se encontró el archivo report.html en /results.{RESET}")


if __name__ == "__main__":
    main()
