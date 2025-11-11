import os
import webbrowser
import subprocess
from pathlib import Path

def run_command(command, description):
    print(f"\n🔹 Ejecutando: {description}...\n{'-' * 50}")
    process = subprocess.run(command, shell=True)
    if process.returncode != 0:
        print(f"❌ Error al ejecutar: {description}")
        exit(process.returncode)
    print(f"✅ {description} completado correctamente.")

def main():
    base_dir = Path(__file__).resolve().parent.parent
    results_dir = base_dir / "results"
    report_path = results_dir / "report.html"

    # 1️⃣ Entrenar modelo
    run_command("rasa train", "Entrenamiento del modelo")

    # 2️⃣ Ejecutar pruebas automáticas de historias
    run_command("rasa test --stories data/test_encuesta.yml", "Pruebas automáticas de encuesta")

    # 3️⃣ Abrir el reporte en el navegador si existe
    if report_path.exists():
        print(f"\n📊 Abriendo reporte: {report_path}")
        webbrowser.open_new_tab(report_path.as_uri())
    else:
        print("\n⚠️ No se encontró el reporte. Verifica si 'rasa test' generó resultados en la carpeta /results.")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas automáticas del chatbot de satisfacción...\n")
    main()
