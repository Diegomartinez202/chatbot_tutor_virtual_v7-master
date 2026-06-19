import os, re, io, sys

ROOT = "/app"
changed = []

def clean_text(s: str) -> str:
    # Normaliza saltos + quita BOM si lo hubiera
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # Reemplaza comillas tipográficas y NBSP
    s = (s.replace("\u201C", '"').replace("\u201D", '"')
         .replace("\u2018", "'").replace("\u2019", "'")
         .replace("\u00A0", " ").replace("\x7f",""))
    # Quita caracteres de control excepto \n y \t
    s = "".join(
        ch for ch in s
        if ch in ("\n","\t")
        or (32 <= ord(ch) <= 126)
        or (ord(ch) > 126 and ord(ch) not in range(0,32))
    )
    return s

def clean_file(path: str):
    try:
        raw = open(path, "rb").read()
        txt = raw.decode("utf-8-sig", errors="ignore")
        cleaned = clean_text(txt)
        if cleaned != txt:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(cleaned)
            changed.append(path)
    except Exception as e:
        print(f"[WARN] {path}: {e}")

# 1) Limpiar ficheros clave
targets = [
    "/app/domain.yml",
    "/app/data/nlu.yml",
    "/app/data/stories.yml",
    "/app/data/rules.yml",
]
for t in targets:
    clean_file(t)

# 2) Quitar ambigüedades NLU sin tocar la lógica:
#    "sí por favor" y "de acuerdo" -> SOLO en confirmacion_escalar_humano
#    "mejor no"                     -> SOLO en negar_escalar
NLU = "/app/data/nlu.yml"
try:
    L = open(NLU, "r", encoding="utf-8").read().splitlines(True)
    curr = None
    in_examples = False

    # variantes por mojibake
    targets_affirm = {"sí por favor", "sÃ­ por favor", "de acuerdo"}
    targets_deny   = {"mejor no"}

    need_confirm = {"sí por favor", "de acuerdo"}
    need_negar   = {"mejor no"}

    have_confirm = {k: False for k in need_confirm}
    have_negar   = {k: False for k in need_negar}

    out = []
    for ln in L:
        s = ln.strip()
        m = re.match(r"^-+\s*intent:\s*(\S+)\s*$", s)
        if m:
            curr = m.group(1)
            in_examples = False

        if s.endswith("examples: |"):
            in_examples = True
            out.append(ln)
            continue

        if in_examples and s.startswith("- "):
            phrase = s[2:].strip()

            # Eliminar frases de los intents equivocados (duplicadas)
            if curr == "affirm" and phrase in targets_affirm:
                continue
            if curr == "deny" and phrase in targets_deny:
                continue

            # Marcar presencia en los intents correctos
            if curr == "confirmacion_escalar_humano":
                key = "sí por favor" if phrase in {"sí por favor","sÃ­ por favor"} else phrase
                if key in have_confirm:
                    have_confirm[key] = True
            if curr == "negar_escalar" and phrase == "mejor no":
                have_negar["mejor no"] = True

        out.append(ln)

    def insert_phrases(lines, intent, phrases):
        if not phrases:
            return lines
        res = []
        curr = None
        for ln in lines:
            s = ln.strip()
            m = re.match(r"^-+\s*intent:\s*(\S+)\s*$", s)
            if m:
                curr = m.group(1)
            res.append(ln)
            if s.endswith("examples: |") and curr == intent:
                for ph in sorted(phrases):
                    res.append(f"    - {ph}\n")
        return res

    miss_c = {("sí por favor" if k in {"sí por favor","sÃ­ por favor"} else k)
              for k,v in have_confirm.items() if not v}
    miss_n = {k for k,v in have_negar.items() if not v}

    if miss_c:
        out = insert_phrases(out, "confirmacion_escalar_humano", miss_c)
    if miss_n:
        out = insert_phrases(out, "negar_escalar", miss_n)

    if out != L:
        open(NLU, "w", encoding="utf-8", newline="\n").writelines(out)
        changed.append(NLU)

except FileNotFoundError:
    pass

print("LIMPIADOS/ACTUALIZADOS:")
print("\n".join(f" - {c}" for c in changed) if changed else " (ninguno)")








