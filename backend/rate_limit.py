# backend/rate_limit.py
"""
Puente para usar decoradores de rate limit sin importar desde main.py.
- Si SlowAPI está activo, expose @limit(...) real.
- Si NO está activo, el decorador es NO-OP (no hace nada).
"""

from typing import Callable, Optional

try:
    from slowapi import Limiter  # type: ignore
except Exception:
    Limiter = None  # type: ignore

_limiter: Optional["Limiter"] = None

def set_limiter(lim) -> None:
    """Lo llama main.py cuando inicializa SlowAPI."""
    global _limiter
    _limiter = lim

def limit(rule: str) -> Callable:
    """
    Uso en routers:
        from backend.rate_limit import limit
        @router.post("/api/chat")
        @limit("60/minute")
        def send_message(...): ...
    """
    if _limiter is None:
        # Decorador no-op si SlowAPI no está activo
        def _noop(fn): return fn
        return _noop
    return _limiter.limit(rule)
