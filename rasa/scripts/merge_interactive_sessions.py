#!/usr/bin/env python
import os
from pathlib import Path
from ruamel.yaml import YAML

BASE_DIR = Path("/app")  # dentro del contenedor
DATA_DIR = BASE_DIR / "data"
INTERACTIVE_ROOT = DATA_DIR / "interactive"
BASE_NLU = DATA_DIR / "nlu.yml"
BASE_STORIES = DATA_DIR / "stories.yml"

yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False

def load_yaml(path):
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.load(f) or {}

def save_yaml(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)

def merge_nlu():
    print("[merge] 🔍 Procesando NLU...")
    base_data = load_yaml(BASE_NLU)
    base_nlu = base_data.get("nlu", [])

    # índice de ejemplos existentes: (intent, text)
    existing_examples = set()
    for item in base_nlu:
        if isinstance(item, dict) and item.get("intent") and item.get("examples"):
            # ejemplos en formato listado multilinea, los normalizamos a líneas
            examples_text = item["examples"]
            if isinstance(examples_text, str):
                lines = [l.strip("- ").strip() for l in examples_text.splitlines() if l.strip()]
                for text in lines:
                    existing_examples.add((item["intent"], text))

    # buscamos todas las sesiones
    if not INTERACTIVE_ROOT.is_dir():
        print(f"[merge] ⚠️ No existe {INTERACTIVE_ROOT}, nada que unir para NLU.")
        return

    for session_dir in sorted(INTERACTIVE_ROOT.glob("session_*")):
        nlu_file = session_dir / "nlu.yml"
        if not nlu_file.is_file():
            continue

        print(f"[merge] ➕ Leyendo NLU de sesión: {nlu_file}")
        session_data = load_yaml(nlu_file)
        session_nlu = session_data.get("nlu", [])

        for item in session_nlu:
            if not isinstance(item, dict):
                continue
            intent = item.get("intent")
            examples_text = item.get("examples")
            if not intent or not examples_text:
                continue

            # convertir bloque de texto a lista de ejemplos
            if isinstance(examples_text, str):
                lines = [l.strip("- ").strip() for l in examples_text.splitlines() if l.strip()]
            elif isinstance(examples_text, list):
                lines = [str(l).strip() for l in examples_text if str(l).strip()]
            else:
                continue

            # nuevo item que iremos rellenando con ejemplos no duplicados
            new_lines = []
            for text in lines:
                key = (intent, text)
                if key not in existing_examples:
                    existing_examples.add(key)
                    new_lines.append(text)

            if new_lines:
                # agregamos este intent con ejemplos nuevos al conjunto base
                examples_block = "\n".join([f"- {t}" for t in new_lines])
                base_nlu.append({"intent": intent, "examples": examples_block})

    base_data["nlu"] = base_nlu
    save_yaml(base_data, BASE_NLU)
    print(f"[merge] ✅ NLU fusionado en {BASE_NLU}")

def normalize_story_steps(steps):
    """Normaliza pasos de una historia a una tupla para poder comparar."""
    norm = []
    for s in steps or []:
        if not isinstance(s, dict):
            continue
        # guardamos la clave principal y su valor como representación
        if "intent" in s:
            norm.append(("intent", s["intent"]))
        elif "action" in s:
            norm.append(("action", s["action"]))
        elif "slot_was_set" in s:
            norm.append(("slot_was_set", tuple(sorted(s["slot_was_set"][0].items()))))
        else:
            # otras estructuras
            norm.append(("raw", tuple(sorted(s.items()))))
    return tuple(norm)

def merge_stories():
    print("[merge] 🔍 Procesando stories...")
    base_data = load_yaml(BASE_STORIES)
    base_stories = base_data.get("stories", [])

    existing_stories = set()
    for s in base_stories:
        if not isinstance(s, dict):
            continue
        name = s.get("story") or s.get("name")
        steps = s.get("steps", [])
        norm = (name, normalize_story_steps(steps))
        existing_stories.add(norm)

    if not INTERACTIVE_ROOT.is_dir():
        print(f"[merge] ⚠️ No existe {INTERACTIVE_ROOT}, nada que unir para stories.")
        return

    for session_dir in sorted(INTERACTIVE_ROOT.glob("session_*")):
        stories_file = session_dir / "stories.yml"
        if not stories_file.is_file():
            continue

        print(f"[merge] ➕ Leyendo stories de sesión: {stories_file}")
        session_data = load_yaml(stories_file)
        session_stories = session_data.get("stories", [])

        for s in session_stories:
            if not isinstance(s, dict):
                continue
            name = s.get("story") or s.get("name")
            steps = s.get("steps", [])
            norm = (name, normalize_story_steps(steps))
            if norm not in existing_stories:
                existing_stories.add(norm)
                base_stories.append(s)

    base_data["stories"] = base_stories
    save_yaml(base_data, BASE_STORIES)
    print(f"[merge] ✅ Stories fusionadas en {BASE_STORIES}")

def main():
    print("[merge] 🔁 Iniciando fusión de sesiones interactivas...")
    merge_nlu()
    merge_stories()
    print("[merge] 🎉 Proceso de fusión completado.")

if __name__ == "__main__":
    main()
