import json
import csv
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), "../data/encuestas.json")

def cargar_encuestas():
    if not os.path.exists(DATA_FILE):
        print("⚠️ No se encontró el archivo de encuestas.")
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_csv(encuestas, archivo_salida="encuestas_export.csv"):
    with open(archivo_salida, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=encuestas[0].keys())
        writer.writeheader()
        writer.writerows(encuestas)
    print(f"✅ Archivo CSV exportado como {archivo_salida}")

def ver_resumen(encuestas):
    total = len(encuestas)
    if total == 0:
        print("No hay encuestas registradas.")
        return
    conteo = {}
    for e in encuestas:
        nivel = e.get("nivel_satisfaccion", "sin_dato")
        conteo[nivel] = conteo.get(nivel, 0) + 1
    print("\n📊 Resumen general:")
    for nivel, cantidad in conteo.items():
        print(f"  - {nivel}: {cantidad} respuestas")
    print(f"  Total: {total}")

def filtrar_por_nivel(encuestas):
    nivel = input("Ingrese el nivel de satisfacción a filtrar: ").strip().lower()
    filtradas = [e for e in encuestas if e.get("nivel_satisfaccion", "").lower() == nivel]
    print(f"\n🔍 Resultados para '{nivel}': {len(filtradas)} registros\n")
    for e in filtradas:
        print(f"- Usuario: {e.get('usuario')} | Comentario: {e.get('comentario')}")

def menu():
    encuestas = cargar_encuestas()
    while True:
        print("\n📋 MENÚ DE ENCUESTAS")
        print("1. Ver resumen general")
        print("2. Filtrar por nivel")
        print("3. Exportar a CSV")
        print("4. Salir")
        opcion = input("Seleccione una opción: ").strip()
        if opcion == "1":
            ver_resumen(encuestas)
        elif opcion == "2":
            filtrar_por_nivel(encuestas)
        elif opcion == "3":
            if encuestas:
                guardar_csv(encuestas)
            else:
                print("⚠️ No hay datos para exportar.")
        elif opcion == "4":
            print("👋 ¡Hasta pronto!")
            break
        else:
            print("Opción no válida. Intente nuevamente.")

if __name__ == "__main__":
    menu()
