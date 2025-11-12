#!/usr/bin/env python3
import os, sys, hashlib, shutil, datetime, re, pathlib, subprocess

# ------------------------------------------------------------
# 🧩 Script de fusión y deduplicación de archivos interactivos
# ------------------------------------------------------------

ROOT = pathlib.Path(__file__).resolve().parents[1]  # .../rasa
INTER = ROOT / "interactive"
DATA_NLU = ROOT / "data" / "nlu"
DATA_STORIES = ROOT / "data" / "stories"
DATA_RULES = ROOT / "data" / "rules"
BACKUP_DIR = ROOT / "backups" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

FILES = [
    ("nlu_interactive.yml", DATA_NLU, "nlu_interactive"),
    ("stories_interactive.yml", DATA_STORIES, "stories_interactive"),
    ("rules_interactive.yml", DATA_RULES, "rules_interactive"),
]

VERSION_HEADER = 'version: "3.1"'

# Colores para logs
C = {
    "ok": "\033[92m",
    "warn": "\033[93m",
    "err": "\033[91m",
    "reset": "\033[0m",
    "info": "\033[94m"
}


def log_info(msg): print(f"{C['info']}ℹ️ {msg}{C['reset']}")
def log_ok(msg): print(f"{C['ok']}✅ {msg}{C['reset']}")
def log_warn(msg): print(f"{C['warn']}⚠️ {msg}{C['reset']}")
def log_err(msg): print(f"{C['err']}❌ {msg}{C['reset']}")


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


def backup_if_exists(path: pathlib.Path):
    """Copia archivos originales a /backups antes de modificarlos."""
    if path.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, BACKUP_DIR / path.name)


def run_cmd(cmd: str, desc: str):
    log_info(desc)
    try:
        subprocess.run(cmd, shell=True, check=True)
        log_ok(f"{desc} completado correctamente.")
    except subprocess.CalledProcessError:
        log_err(f"Fallo en: {desc}")
        sys.exit(1)


def main():
    moved_any = False
    for fname, out_dir, base in FILES:
        src = INTER / fname
        if not (src.exists() and src.stat().st_size > 0):
            log_warn(f"Omitido (no existe o está vacío): {src}")
            continue

        log_info(f"Procesando {src.name} ...")
        raw = read_text(src)
        raw = ensure_header(raw)

        # deduplicar bloques
        blocks = splitter_blocks(raw)
        seen = set()
        unique_blocks = []
        for b in blocks:
            h = sha256_text(b)
            if h not in seen:
                seen.add(h)
                unique_blocks.append(b)
        merged = ("\n\n".join(unique_blocks)).strip() + "\n"

        # copia de seguridad
        backup_if_exists(src)
        dst = write_unique(out_dir, base, merged)
        log_ok(f"Copiado con deduplicación: {src} → {dst}")
        moved_any = True

    if not moved_any:
        log_info("Nada que mover o fusionar. Directorio vacío.")
        sys.exit(0)

    # validación y entrenamiento
    run_cmd(f"cd {ROOT} && rasa data validate", "Validando datos")
    run_cmd(f"cd {ROOT} && rasa train", "Entrenando modelo")

    # limpieza opcional del directorio interactive
    try:
        log_info("Limpiando archivos temporales de interactive/ ...")
        for f in INTER.glob("*_interactive.yml"):
            f.unlink(missing_ok=True)
        log_ok("Directorio interactive/ limpio.")
    except Exception as e:
        log_warn(f"No se pudieron limpiar archivos: {e}")


if __name__ == "__main__":
    main()
