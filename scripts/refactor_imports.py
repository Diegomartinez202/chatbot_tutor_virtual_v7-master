import os
import re
import argparse
from typing import Tuple, Optional

BASE_DIR = "backend"

# Directorios a excluir por seguridad (aunque solo procesamos backend/)
EXCLUDE_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".venv", "venv", "env", "node_modules", "frontend", "admin-panel-react",
    "dist", "build", ".idea", ".vscode", "notebooks", "tests_artifacts"
}

# Patrones de reemplazo a formato compacto
REPLACE_PATTERNS = {
    r"from backend\.schemas\.\w+ import ": "from backend.schemas import ",
    r"from backend\.models\.\w+ import ": "from backend.models import ",
    r"from backend\.services\.\w+ import ": "from backend.services import ",
    r"from backend\.utils\.\w+ import ": "from backend.utils import ",
}

# Patrón para detectar líneas de import que queremos deduplicar
IMPORT_LINE_RE = re.compile(
    r"^\s*from\s+backend\.(schemas|models|services|utils)\s+import\s+.+$"
)

JWT_FUNCS = [
    "create_access_token", "create_refresh_token",
    "decode_access_token", "decode_refresh_token",
    "decode_token", "reissue_tokens_from_refresh",
]

def read_text_best_effort(path: str) -> Tuple[str, Optional[str]]:
    """
    Lee el archivo intentando varias codificaciones.
    Devuelve (contenido, encoding_usada).
    """
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read(), enc
        except UnicodeDecodeError:
            continue
    # Último recurso: ignorar errores (evita romperse por un byte raro)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read(), "utf-8"

def write_text(path: str, content: str, encoding: Optional[str]) -> None:
    enc = encoding or "utf-8"
    with open(path, "w", encoding=enc) as f:
        f.write(content)

def apply_basic_replacements(content: str) -> str:
    for pattern, repl in REPLACE_PATTERNS.items():
        content = re.sub(pattern, repl, content)
    return content

def promote_jwt_module_usage(content: str) -> str:
    """
    Opcional: convierte imports sueltos de funciones JWT en import del módulo jwt_manager
    y prefixea los llamados (create_access_token -> jwt_manager.create_access_token).
    """
    # 1) Reemplazar líneas de import de funciones sueltas por import del módulo
    content = re.sub(
        r"^\s*from\s+backend\.utils\s+import\s+(" + "|".join(JWT_FUNCS) + r")(?:\s*,\s*(" + "|".join(JWT_FUNCS) + r"))*\s*$",
        "from backend.utils import jwt_manager",
        content,
        flags=re.MULTILINE
    )
    # 2) Prefix a las llamadas de función
    for func in JWT_FUNCS:
        content = re.sub(rf"\b{func}\s*\(", f"jwt_manager.{func}(", content)
    return content

def dedupe_import_lines(content: str) -> str:
    """
    Elimina líneas EXACTAMENTE duplicadas de import de backend.(schemas|models|services|utils),
    preservando el primer encuentro y el orden.
    No mergea múltiples importaciones diferentes; solo quita duplicados exactos.
    """
    lines = content.splitlines()
    seen = set()
    out = []
    for line in lines:
        if IMPORT_LINE_RE.match(line):
            if line not in seen:
                seen.add(line)
                out.append(line)
            else:
                # línea duplicada exacta -> se omite
                continue
        else:
            out.append(line)
    return "\n".join(out) + ("\n" if content.endswith("\n") else "")

def should_skip_dir(dir_name: str) -> bool:
    return dir_name in EXCLUDE_DIRS

def refactor_imports(base_dir=BASE_DIR, dry_run=False, keep_jwt_functions=False):
    modified = []
    for root, dirs, files in os.walk(base_dir):
        # Filtrar directorios no deseados
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]

        for file in files:
            if not file.endswith(".py"):
                continue
            file_path = os.path.join(root, file)

            # Seguridad extra: solo bajo backend/
            if not os.path.relpath(file_path).startswith(BASE_DIR):
                continue

            original, enc = read_text_best_effort(file_path)
            new = original

            # 1) Reemplazos básicos -> imports compactos
            new = apply_basic_replacements(new)

            # 2) (Opcional) Promover uso por módulo para JWT
            if not keep_jwt_functions:
                new = promote_jwt_module_usage(new)

            # 3) Deduplicar líneas de import exactas
            new = dedupe_import_lines(new)

            if new != original:
                modified.append(file_path)
                if not dry_run:
                    write_text(file_path, new, enc)

    if modified:
        print("\n✅ Archivos modificados:\n")
        for p in modified:
            print(" -", p)
        if dry_run:
            print("\n🟡 Modo simulación: no se escribieron cambios.")
        else:
            print("\n💾 Cambios aplicados correctamente.")
    else:
        print("\nℹ️ No se encontraron cambios que aplicar.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Refactoriza imports en backend/ de forma segura.")
    parser.add_argument("--dry-run", action="store_true", help="Simula los cambios sin escribirlos.")
    parser.add_argument(
        "--keep-jwt-functions",
        action="store_true",
        help="No convierte funciones JWT sueltas a `from backend.utils import jwt_manager`."
    )
    args = parser.parse_args()

    refactor_imports(
        base_dir=BASE_DIR,
        dry_run=args.dry_run,
        keep_jwt_functions=args.keep_jwt_functions
    )