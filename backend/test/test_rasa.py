import yaml
from pathlib import Path

def test_nlu_examples():
    path = Path("../../rasa/data/nlu.yml")
    assert path.exists(), "❌ El archivo nlu.yml no existe"

    with open(path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    assert "nlu" in data, "❌ La clave 'nlu' no está en el archivo"
    assert len(data["nlu"]) > 0, "❌ No hay intents en el archivo nlu.yml"

    print("✅ Archivo nlu.yml cargado correctamente con intents")

if __name__ == "__main__":
    test_nlu_examples()
