#!/bin/bash

# Verificar si el contenedor 'rasa' está en ejecución
if ! docker ps --format '{{.Names}}' | grep -q '^rasa$'; then
  echo "El contenedor 'rasa' no está en ejecución. Por favor, inícialo antes de continuar."
  exit 1
fi

docker exec -i rasa sh -c "cat > /tmp/clean_yaml.py" <<'PY'
import os
ROOT = "/app"
changed = []
def clean_text(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = (s.replace("\u201C", '"').replace("\u201D", '"')
           .replace("\u2018", "'").replace("\u2019", "'")
           .replace("\u00A0", " "))
    s = "".join(ch for ch in s if ch in ("\n","\t") or (32 <= ord(ch) <= 126) or (ord(ch) > 126 and ord(ch) not in range(0,32)))
    return s
for dirpath, _, filenames in os.walk(ROOT):
    for name in filenames:
        if name.lower().endswith((".yml", ".yaml")):
            p = os.path.join(dirpath, name)
            with open(p, "rb") as f:
                raw = f.read()
            txt = raw.decode("utf-8-sig", errors="ignore")
            cleaned = clean_text(txt)
            if cleaned != txt:
                with open(p, "w", encoding="utf-8", newline="\n") as f:
                    f.write(cleaned)
                changed.append(p)
print("LIMPIADOS:"); [print(" -",c) for c in changed] or print(" (ninguno)")
PY

docker exec rasa python /tmp/clean_yaml.py