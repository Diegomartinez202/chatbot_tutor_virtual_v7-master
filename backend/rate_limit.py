# backend/rate_limit.py
"""
Lightweight adapter for request rate limiting.

- set_limiter(limiter): register an object that implements .limit(rule) -> decorator.
- get_limiter(): returns the currently registered limiter (or None).
- limit(rule): returns a decorator. If a real limiter is set and exposes .limit,
  that decorator is used; otherwise a no-op decorator is returned.
"""

import functools
from typing import Any, Callable, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

_limiter: Optional[Any] = None

def set_limiter(limiter: Any) -> None:
    global _limiter
    _limiter = limiter

def get_limiter() -> Optional[Any]:
    return _limiter

def _noop_limit(rule: str) -> Callable[[F], F]:
    def _decorator(fn: F) -> F:
        return fn
    return _decorator  # type: ignore[return-value]

def limit(rule: str) -> Callable[[F], F]:
    if _limiter is not None and hasattr(_limiter, "limit"):
        try:
            return _limiter.limit(rule)  # type: ignore[return-value]
        except Exception:
            return _noop_limit(rule)
    return _noop_limit(rule)

__all__ = ["set_limiter", "get_limiter", "limit"]