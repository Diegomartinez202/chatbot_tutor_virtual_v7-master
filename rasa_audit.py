import yaml
import os
from collections import defaultdict

# ============================================================
# UTILIDADES
# ============================================================

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def extract_intents(nlu_data):
    intents = set()
    for item in nlu_data.get("nlu", []):
        if "intent" in item:
            intents.add(item["intent"])
    return intents

def extract_stories(stories_data):
    used_intents = set()
    used_actions = set()

    for story in stories_data.get("stories", []):
        steps = story.get("steps", [])
        for step in steps:
            if "intent" in step:
                used_intents.add(step["intent"])
            if "action" in step:
                used_actions.add(step["action"])

    return used_intents, used_actions


def extract_rules(rules_data):
    used_intents = set()
    used_actions = set()

    for rule in rules_data.get("rules", []):
        steps = rule.get("steps", [])
        for step in steps:
            if "intent" in step:
                used_intents.add(step["intent"])
            if "action" in step:
                used_actions.add(step["action"])

    return used_intents, used_actions


def extract_domain(domain_data):
    intents = set(domain_data.get("intents", []))
    actions = set(domain_data.get("actions", []))
    slots = set(domain_data.get("slots", {}).keys())
    responses = set(domain_data.get("responses", {}).keys())

    return intents, actions, slots, responses


# ============================================================
# DETECCIÓN LLM (REEMPLAZO OBLIGATORIO)
# ============================================================

def detect_llm_usage(domain_data, stories_data, rules_data):
    llm_flags = []

    keywords = ["llm", "gpt", "openai", "chatgpt", "agent", "langchain"]

    def scan(obj, source):
        if isinstance(obj, dict):
            for k, v in obj.items():
                scan(k, source)
                scan(v, source)
        elif isinstance(obj, list):
            for i in obj:
                scan(i, source)
        elif isinstance(obj, str):
            lower = obj.lower()
            if any(k in lower for k in keywords):
                llm_flags.append((source, obj))

    scan(domain_data, "domain")
    scan(stories_data, "stories")
    scan(rules_data, "rules")

    return llm_flags


# ============================================================
# BOTONES Y REDIRECCIONES (CRÍTICO EN RASA UI)
# ============================================================

def extract_buttons(domain_data):
    buttons_map = defaultdict(list)

    responses = domain_data.get("responses", {})

    for resp_name, content in responses.items():
        for item in content:
            if "buttons" in item:
                for btn in item["buttons"]:
                    buttons_map[resp_name].append({
                        "title": btn.get("title"),
                        "payload": btn.get("payload")
                    })

    return buttons_map


# ============================================================
# AUDITOR PRINCIPAL
# ============================================================

def audit(domain_path, nlu_path, stories_path, rules_path):

    domain = load_yaml(domain_path)
    nlu = load_yaml(nlu_path)
    stories = load_yaml(stories_path)
    rules = load_yaml(rules_path)

    domain_intents, domain_actions, domain_slots, domain_responses = extract_domain(domain)

    nlu_intents = extract_intents(nlu)

    story_intents, story_actions = extract_stories(stories)
    rule_intents, rule_actions = extract_rules(rules)

    used_intents = nlu_intents | story_intents | rule_intents
    used_actions = story_actions | rule_actions

    # ========================================================
    # INCONSISTENCIAS
    # ========================================================

    unused_intents = domain_intents - used_intents
    missing_intents = used_intents - domain_intents

    unused_actions = domain_actions - used_actions
    missing_actions = used_actions - domain_actions

    unused_slots = domain_slots  # simplificado (mejorable con tracker)
    unused_responses = domain_responses  # refinable

    # ========================================================
    # LLM DETECTION
    # ========================================================

    llm_flags = detect_llm_usage(domain, stories, rules)

    # ========================================================
    # BOTONES
    # ========================================================

    buttons = extract_buttons(domain)

    # ========================================================
    # REPORTE
    # ========================================================

    print("\n==============================")
    print("🔴 RASA AUDIT REPORT")
    print("==============================\n")

    print("❌ INTENTS A ELIMINAR:")
    for i in sorted(unused_intents):
        print(f" - {i}")

    print("\n❌ ACTIONS A ELIMINAR:")
    for a in sorted(unused_actions):
        print(f" - {a}")

    print("\n⚠ INTENTS FALTANTES EN DOMAIN:")
    for i in sorted(missing_intents):
        print(f" - {i}")

    print("\n⚠ ACTIONS FALTANTES EN DOMAIN:")
    for a in sorted(missing_actions):
        print(f" - {a}")

    print("\n🤖 LLM DETECTADO (REEMPLAZAR O REFACTORIZAR):")
    for src, val in llm_flags:
        print(f" - [{src}] {val}")

    print("\n🔘 BOTONES DETECTADOS (REVISAR REDIRECCIÓN):")
    for resp, btns in buttons.items():
        print(f"\n {resp}:")
        for b in btns:
            print(f"   -> {b['title']} => {b['payload']}")

    print("\n==============================")
    print("✔ AUDITORÍA FINALIZADA")
    print("==============================\n")


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    audit(
        "data/domain.yml",
        "data/nlu.yml",
        "data/stories.yml",
        "data/rules.yml"
    )