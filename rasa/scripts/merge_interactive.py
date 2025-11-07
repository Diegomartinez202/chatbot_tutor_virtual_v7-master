#!/usr/bin/env python3
import os, sys, hashlib, shutil, datetime, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]  # .../rasa
INTER = ROOT / "interactive"
DATA_NLU = ROOT / "data" / "nlu"
DATA_STORIES = ROOT / "data" / "stories"
DATA_RULES = ROOT / "data" / "rules"

FILES = [
    ("nlu_interactive.yml", DATA_NLU, "nlu_interactive"),
    ("stories_interactive.yml", DATA_STORIES, "stories_interactive"),
    ("rules_interactive.yml", DATA_RULES, "rules_interactive"),
]

VERSION_HEADER = 'version: "3.1"'

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

def read_text(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

def ensure_header(text: str) -> str:
    t = text.strip()
    if not t.startswith("version:"):
        return VERSION_HEADER + "\n\n" + t + "\n"
    return text

def splitter_blocks(text: str) -> list[str]:
    parts = re.split(r'\n(?=nlu:|stories:|rules:)', text, flags=re.IGNORECASE)
    if len(parts) > 1:
        head = parts[0]
        rest = parts[1:]
        rebuilt = [head]
        for r in rest:
            rebuilt.append("\n" + r.strip())
        parts = rebuilt
    return [p.strip() for p in parts if p.strip()]

def write_unique(dst_dir: pathlib.Path, base_name: str, content: str) -> str:
    dst_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = dst_dir / f"{base_name}_{ts}.yml"
    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)
    return str(dst)

def main():
    moved_any = False
    for fname, out_dir, base in FILES:
        src = INTER / fname
        if not (src.exists() and src.stat().st_size > 0):
            print(f"⚠️  Omitido (no existe/está vacío): {src}")
            continue

        raw = read_text(src)
        raw = ensure_header(raw)

        blocks = splitter_blocks(raw)
        seen = set()
        unique_blocks = []
        for b in blocks:
            h = sha256_text(b)
            if h not in seen:
                seen.add(h)
                unique_blocks.append(b)
        merged = ("\n\n".join(unique_blocks)).strip() + "\n"

        dst = write_unique(out_dir, base, merged)
        print(f"➡️  Copiado con dedup: {src}  →  {dst}")
        moved_any = True

    if not moved_any:
        print("ℹ️  Nada para mover.")
        sys.exit(0)

    try:
        print("🔎 Validando datos (rasa data validate)...")
        os.system(f"cd {ROOT} && rasa data validate")
        print("🧠 Entrenando modelo (rasa train)...")
        os.system(f"cd {ROOT} && rasa train")
    except Exception as e:
        print(f"❌ Error al validar/entrenar: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
