# rasa/tools/sanity_check.py
# Verifica:
# 1) Intents definidos en domain vs usados en stories/rules/NLU
# 2) Utterances (responses) definidas vs usadas en stories/rules
# 3) Ejemplos NLU duplicados con intent distinto

import os, sys, re, glob
from typing import Set, Dict, List
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOMAIN_DIR = os.path.join(ROOT, "domain")
DATA_DIR = os.path.join(ROOT, "data")

def load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def iter_yaml_files(folder: str) -> List[str]:
    return [p for p in glob.glob(os.path.join(folder, "**", "*.yml"), recursive=True)]

def get_domain_intents_and_responses() -> (Set[str], Set[str]):
    intents: Set[str] = set()
    responses: Set[str] = set()
    for yml in iter_yaml_files(DOMAIN_DIR):
        doc = load_yaml(yml)
        # intents
        for it in doc.get("intents", []) or []:
            if isinstance(it, str):
                intents.add(it)
            elif isinstance(it, dict):
                intents.add(list(it.keys())[0])
        # responses
        resp = doc.get("responses", {}) or {}
        for rname in resp.keys():
            responses.add(rname)
    return intents, responses

def extract_intents_from_stories_like(doc: dict) -> Set[str]:
    used: Set[str] = set()
    if not isinstance(doc, dict):
        return used
    stories = doc.get("stories") or doc.get("rules") or []
    if not isinstance(stories, list):
        return used
    for st in stories:
        steps = st.get("steps", [])
        for s in steps:
            if "intent" in s:
                used.add(s["intent"])
    return used

def extract_actions_from_stories_like(doc: dict) -> Set[str]:
    used: Set[str] = set()
    if not isinstance(doc, dict):
        return used
    stories = doc.get("stories") or doc.get("rules") or []
    if not isinstance(stories, list):
        return used
    for st in stories:
        steps = st.get("steps", [])
        for s in steps:
            if "action" in s:
                used.add(s["action"])
    return used

def extract_nlu_examples(doc: dict) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    nlu = doc.get("nlu", [])
    if not isinstance(nlu, list):
        return out
    for block in nlu:
        intent = block.get("intent")
        examples = block.get("examples")
        if not intent or not examples:
            continue
        # examples vienen en bloque multilínea con "- "
        lines = []
        for ln in examples.split("\n"):
            ln = ln.strip()
            if ln.startswith("- "):
                ex = ln[2:].strip()
                if ex:
                    lines.append(ex)
        if lines:
            out.setdefault(intent, []).extend(lines)
    return out

def main() -> int:
    if not os.path.isdir(DOMAIN_DIR):
        print(f"[ERROR] No existe carpeta de dominio: {DOMAIN_DIR}")
        return 2
    if not os.path.isdir(DATA_DIR):
        print(f"[ERROR] No existe carpeta data: {DATA_DIR}")
        return 2

    domain_intents, domain_responses = get_domain_intents_and_responses()

    used_intents: Set[str] = set()
    used_actions: Set[str] = set()
    nlu_examples: Dict[str, List[str]] = {}

    for yml in iter_yaml_files(DATA_DIR):
        doc = load_yaml(yml)
        used_intents |= extract_intents_from_stories_like(doc)
        used_actions |= extract_actions_from_stories_like(doc)
        # juntar NLU
        ex = extract_nlu_examples(doc)
        for k, vs in ex.items():
            nlu_examples.setdefault(k, []).extend(vs)

    # 1) intents usados pero NO definidos
    missing_intents = sorted(list(used_intents - domain_intents))
    # 2) utter_ usados (actions que empiezan con utter_) pero NO definidos en responses
    used_utter = sorted([a for a in used_actions if a.startswith("utter_")])
    missing_utters = sorted(list(set(used_utter) - domain_responses))

    # 3) ejemplos duplicados en distintas intents
    ex_to_intents: Dict[str, Set[str]] = {}
    for intent, examples in nlu_examples.items():
        for e in examples:
            ex_to_intents.setdefault(e.lower(), set()).add(intent)
    duplicates = {ex: intents for ex, intents in ex_to_intents.items() if len(intents) > 1}

    print("=== SANITY REPORT ===")
    print(f"- Intents definidos en domain: {len(domain_intents)}")
    print(f"- Utterances definidas en domain.responses: {len(domain_responses)}")
    print(f"- Intents usados en stories/rules: {len(used_intents)}")
    print(f"- Actions usados en stories/rules: {len(used_actions)}")
    print(f"- Intents con ejemplos NLU: {len(nlu_examples)}")
    print()

    exit_code = 0

    if missing_intents:
        exit_code = 1
        print("❌ Intents USADOS pero NO definidos en domain:")
        for it in missing_intents:
            print(f"  - {it}")
        print()

    if missing_utters:
        exit_code = 1
        print("❌ Utterances USADAS pero NO definidas en domain.responses:")
        for ut in missing_utters:
            print(f"  - {ut}")
        print()

    if duplicates:
        exit_code = 1
        print("❌ Ejemplos NLU duplicados con **intents distintos**:")
        for ex, intents in sorted(duplicates.items()):
            print(f'  - "{ex}"  →  {", ".join(sorted(intents))}')
        print()

    if exit_code == 0:
        print("✅ Sanity OK: domain/data consistentes.")

    return exit_code

if __name__ == "__main__":
    sys.exit(main())
