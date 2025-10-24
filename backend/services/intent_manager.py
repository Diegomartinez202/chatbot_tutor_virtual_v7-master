# =====================================================
# 🧩 backend/services/intent_manager.py
# =====================================================
from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Iterable

import yaml  # PyYAML
from backend.config.settings import settings

# ============================
# Helpers robustos para rutas/strings de settings
# ============================

DEFAULT_NLU_FILE = Path("/app/rasa/data/nlu.yml")
DEFAULT_DOMAIN_FILE = Path("/app/rasa/domain.yml")
DEFAULT_TRAIN_CMD = "rasa train"


def _as_str(value: Any, default: str) -> str:
    """
    Convierte un valor en str de forma segura. Si viene un FieldInfo u otro tipo,
    cae al default.
    """
    try:
        if isinstance(value, (str, os.PathLike)):
            return str(value)
        return default
    except Exception:
        return default


def _as_path(value: Any, default: Path) -> Path:
    """
    Convierte un valor en Path de forma segura, con fallback.
    """
    try:
        s = _as_str(value, str(default))
        return Path(s)
    except Exception:
        return default


# ============================
# 📁 Rutas de los archivos Rasa (con coerción segura)
# ============================

NLU_FILE = _as_path(getattr(settings, "rasa_data_path", None), DEFAULT_NLU_FILE)
DOMAIN_FILE = _as_path(getattr(settings, "rasa_domain_path", None), DEFAULT_DOMAIN_FILE)


# ============================
# 🔍 Verificar si un intent ya existe
# ============================

def intent_ya_existe(intent_name: str) -> bool:
    if not NLU_FILE.exists():
        return False
    with open(NLU_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return any(entry.get("intent") == intent_name for entry in data.get("nlu", []))


# ============================
# ➕ Guardar un nuevo intent (API/PANEL)
# ============================

def guardar_intent(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    data = {
        "intent": "nombre_intent",
        "examples": ["frase 1", "frase 2", ...]  # o string con saltos de línea
        "responses": ["respuesta 1", "respuesta 2"]  # o string con saltos / pipes
    }
    """
    intent_name = data["intent"]
    examples: Iterable[str] = data.get("examples") or []
    responses: Iterable[str] = data.get("responses") or []

    # Normalización flexible
    if isinstance(examples, str):
        examples = [ln.strip("- ").strip() for ln in examples.splitlines() if ln.strip()]
    if isinstance(responses, str):
        responses = [ln.strip() for ln in responses.splitlines() if ln.strip()]

    if not NLU_FILE.exists():
        raise FileNotFoundError(f"No existe NLU_FILE: {NLU_FILE}")

    with open(NLU_FILE, "r", encoding="utf-8") as f:
        nlu_data = yaml.safe_load(f) or {}

    nlu_data.setdefault("nlu", []).append({
        "intent": intent_name,
        "examples": "\n".join(f"- {e.strip()}" for e in examples if isinstance(e, str) and e.strip())
    })

    with open(NLU_FILE, "w", encoding="utf-8") as f:
        yaml.dump(nlu_data, f, allow_unicode=True, sort_keys=False)

    agregar_respuesta_en_domain(intent_name, list(responses))
    return {"message": f"✅ Intent '{intent_name}' guardado correctamente"}


# ============================
# 💬 Guardar respuestas en domain.yml
# ============================

def agregar_respuesta_en_domain(intent_name: str, responses: List[str]) -> None:
    if not DOMAIN_FILE.exists():
        raise FileNotFoundError(f"No existe DOMAIN_FILE: {DOMAIN_FILE}")

    with open(DOMAIN_FILE, "r", encoding="utf-8") as f:
        domain_data = yaml.safe_load(f) or {}

    utter_key = f"utter_{intent_name}"
    domain_data.setdefault("responses", {})[utter_key] = [
        {"text": r} for r in responses if isinstance(r, str)
    ]
    if intent_name not in domain_data.get("intents", []):
        domain_data.setdefault("intents", []).append(intent_name)

    with open(DOMAIN_FILE, "w", encoding="utf-8") as f:
        yaml.dump(domain_data, f, allow_unicode=True, sort_keys=False)


# ============================
# 🧠 Entrenamiento automático de Rasa
# ============================

def entrenar_rasa() -> None:
    raw_cmd = getattr(settings, "rasa_train_command", DEFAULT_TRAIN_CMD)
    cmd = _as_str(raw_cmd, DEFAULT_TRAIN_CMD)
    result = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"❌ Error al entrenar Rasa:\n{result.stderr}")
    print("✅ Rasa entrenado exitosamente")


# ============================
# 🗑️ Eliminar intent + respuesta
# ============================

def eliminar_intent(intent_name: str) -> Dict[str, Any]:
    if not NLU_FILE.exists() or not DOMAIN_FILE.exists():
        raise FileNotFoundError("Faltan archivos de configuración")

    # nlu.yml
    with open(NLU_FILE, "r", encoding="utf-8") as f:
        nlu_data = yaml.safe_load(f) or {}
    nlu_data["nlu"] = [
        entry for entry in nlu_data.get("nlu", []) if entry.get("intent") != intent_name
    ]
    with open(NLU_FILE, "w", encoding="utf-8") as f:
        yaml.dump(nlu_data, f, allow_unicode=True, sort_keys=False)

    # domain.yml
    with open(DOMAIN_FILE, "r", encoding="utf-8") as f:
        domain_data = yaml.safe_load(f) or {}
    domain_data["intents"] = [i for i in domain_data.get("intents", []) if i != intent_name]
    domain_data.setdefault("responses", {}).pop(f"utter_{intent_name}", None)

    with open(DOMAIN_FILE, "w", encoding="utf-8") as f:
        yaml.dump(domain_data, f, allow_unicode=True, sort_keys=False)

    return {"message": f"🗑️ Intent '{intent_name}' eliminado correctamente"}


# ============================
# 📄 Obtener lista de intents
# ============================

def obtener_intents() -> List[Dict[str, Any]]:
    if not NLU_FILE.exists():
        return []
    with open(NLU_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("nlu", [])


# ============================
# ♻️ Recarga desde archivos locales
# ============================

def cargar_intents_automaticamente() -> Dict[str, Any]:
    if not NLU_FILE.exists() or not DOMAIN_FILE.exists():
        raise FileNotFoundError("Archivos de entrenamiento no encontrados")
    intents = obtener_intents()
    return {"message": f"♻️ {len(intents)} intents recargados correctamente"}


# ============================
# ✏️ Actualizar un intent existente
# ============================

def actualizar_intent(intent_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    if not NLU_FILE.exists() or not DOMAIN_FILE.exists():
        raise FileNotFoundError("Faltan archivos necesarios para actualizar el intent")

    examples = data.get("examples", [])
    responses = data.get("responses", [])

    if not examples or not all(isinstance(e, str) and e.strip() for e in examples):
        raise ValueError("Debe proporcionar ejemplos válidos y no vacíos")
    if not responses or not all(isinstance(r, str) and r.strip() for r in responses):
        raise ValueError("Debe proporcionar respuestas válidas y no vacías")

    # Actualizar nlu.yml
    with open(NLU_FILE, "r", encoding="utf-8") as f:
        nlu_data = yaml.safe_load(f) or {}
    nlu_list = nlu_data.get("nlu", [])
    intent_encontrado = False
    for i, entry in enumerate(nlu_list):
        if entry.get("intent") == intent_name:
            nlu_list[i]["examples"] = "\n".join(f"- {e.strip()}" for e in examples)
            intent_encontrado = True
            break
    if not intent_encontrado:
        raise ValueError(f"No se encontró el intent '{intent_name}'")

    with open(NLU_FILE, "w", encoding="utf-8") as f:
        yaml.dump({"nlu": nlu_list}, f, allow_unicode=True, sort_keys=False)

    # Actualizar domain.yml
    with open(DOMAIN_FILE, "r", encoding="utf-8") as f:
        domain_data = yaml.safe_load(f) or {}

    utter_key = f"utter_{intent_name}"
    domain_data.setdefault("responses", {})[utter_key] = [{"text": r.strip()} for r in responses]
    if intent_name not in domain_data.get("intents", []):
        domain_data.setdefault("intents", []).append(intent_name)

    with open(DOMAIN_FILE, "w", encoding="utf-8") as f:
        yaml.dump(domain_data, f, allow_unicode=True, sort_keys=False)

    return {
        "intent": intent_name,
        "examples": list(examples),
        "responses": list(responses),
        "message": "✅ Intent actualizado correctamente",
    }


# ============================
# 📥 Cargar intents desde CSV/JSON subido (bulk)
# ============================

def cargar_intents(items: Any) -> Dict[str, Any]:
    """
    Acepta lista de dicts (de JSON o CSV.DictReader) con claves:
      - intent (str)
      - examples (str con líneas o lista[str])
      - responses (str con líneas o separadas por |, o lista[str])
    Crea intents que no existan. No elimina ni reescribe.
    """
    if not isinstance(items, list):
        raise ValueError("Se esperaba una lista de intents.")

    creados = 0
    saltados = 0
    for row in items:
        intent = (row.get("intent") or "").strip()
        if not intent:
            saltados += 1
            continue

        if intent_ya_existe(intent):
            saltados += 1
            continue

        examples = row.get("examples") or []
        responses = row.get("responses") or []

        if isinstance(examples, str):
            if "|" in examples:
                examples = [x.strip() for x in examples.split("|") if x.strip()]
            else:
                examples = [ln.strip("- ").strip() for ln in examples.splitlines() if ln.strip()]

        if isinstance(responses, str):
            if "|" in responses:
                responses = [x.strip() for x in responses.split("|") if x.strip()]
            else:
                responses = [ln.strip() for ln in responses.splitlines() if ln.strip()]

        guardar_intent({"intent": intent, "examples": examples, "responses": responses})
        creados += 1

    return {"message": f"✅ Intents procesados. Creados: {creados}, saltados: {saltados}"}


# ============================
# 📤 Exportar intents a CSV
# ============================

def exportar_intents_csv():
    """
    Devuelve un stream (StringIO) con CSV:
    intent,examples,responses
    """
    from io import StringIO

    # Cargar NLU
    nlu = []
    if NLU_FILE.exists():
        with open(NLU_FILE, "r", encoding="utf-8") as f:
            nlu_data = yaml.safe_load(f) or {}
            nlu = nlu_data.get("nlu", [])

    # Cargar DOMAIN para respuestas
    responses_map: Dict[str, List[str]] = {}
    if DOMAIN_FILE.exists():
        with open(DOMAIN_FILE, "r", encoding="utf-8") as f:
            domain_data = yaml.safe_load(f) or {}
            resp = domain_data.get("responses", {}) or {}
            for k, v in resp.items():
                if not k.startswith("utter_"):
                    continue
                intent = k.replace("utter_", "", 1)
                texts = []
                for item in (v or []):
                    t = item.get("text")
                    if isinstance(t, str):
                        texts.append(t)
                responses_map[intent] = texts

    out = StringIO()
    out.write("intent,examples,responses\n")
    for entry in nlu:
        it = entry.get("intent")
        ex_raw = entry.get("examples") or ""
        examples_list = [
            ln.strip("- ").strip()
            for ln in str(ex_raw).splitlines()
            if ln.strip()
        ]
        resp_list = responses_map.get(it, [])
        out.write(
            f"{it},\"{' | '.join(examples_list)}\",\"{' | '.join(resp_list)}\"\n"
        )

    out.seek(0)
    return out


# Back-compat: algunos controladores usaban este nombre
def guardar_intent_csv():
    """Wrapper de compatibilidad: retorna el stream CSV de exportación."""
    return exportar_intents_csv()
