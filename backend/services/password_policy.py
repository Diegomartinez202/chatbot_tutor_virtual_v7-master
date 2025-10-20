# backend/services/password_policy.py
from __future__ import annotations

import re
from typing import Tuple, List, Optional

MIN_LEN = 8
RE_UPPER = re.compile(r"[A-Z]")
RE_LOWER = re.compile(r"[a-z]")
RE_DIGIT = re.compile(r"[0-9]")
RE_SPECIAL = re.compile(r"[^\w]")

BANNED = {
    "password", "contraseña", "12345678", "qwerty", "admin", "zajuna", "abc123", "11111111"
}

def validate_password(pw: str, *, email: Optional[str] = None, name: Optional[str] = None) -> Tuple[bool, List[str]]:
    errs: List[str] = []
    if not pw or len(pw) < MIN_LEN:
        errs.append(f"Debe tener al menos {MIN_LEN} caracteres.")
    if not RE_UPPER.search(pw):
        errs.append("Debe incluir al menos una letra mayúscula.")
    if not RE_LOWER.search(pw):
        errs.append("Debe incluir al menos una letra minúscula.")
    if not RE_DIGIT.search(pw):
        errs.append("Debe incluir al menos un número.")
    if not RE_SPECIAL.search(pw):
        errs.append("Debe incluir al menos un carácter especial (por ejemplo: !@#$%&*).")

    low = pw.lower()
    if low in BANNED:
        errs.append("La contraseña es demasiado común.")
    # evitar contener email o nombre
    if email and email.split("@", 1)[0].lower() in low:
        errs.append("No debe contener tu email o parte de él.")
    if name:
        parts = [p for p in re.split(r"\s+", name.strip().lower()) if p]
        if any(p and p in low for p in parts):
            errs.append("No debe contener tu nombre.")

    return (len(errs) == 0, errs)

def policy_snapshot():
    return {
        "min_length": MIN_LEN,
        "requires": ["uppercase", "lowercase", "digit", "special"],
        "banned_examples": sorted(list(BANNED))[:5],
    }