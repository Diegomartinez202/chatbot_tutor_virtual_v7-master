# backend/rate_limit.py
"""
Adapter for request rate limiting.

- If a limiter with `.limit` (e.g., slowapi.Limiter) is available, register it
  via `set_limiter(limiter)` and use its @limit decorator.
- If there is no limiter or rate limiting is disabled, @limit returns a no-op
  decorator that leaves the function unchanged.
"""

from __future__ import annotations

import functools
import os
from typing import Any, Callable, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

_limiter: Optional[Any] = None


def set_limiter(limiter: Any) -> None:
    """
    Register a limiter instance (for example slowapi.Limiter).
    Called from main.py during startup if SlowAPI is enabled.
    """
    global _limiter
    _limiter = limiter


def get_limiter() -> Optional[Any]:
    """Return the currently configured limiter (or None)."""
    return _limiter


def _rate_limit_enabled() -> bool:
    """
    Check if rate limiting is enabled via environment variables.
    Defaults to enabled unless RATE_LIMIT_ENABLED="false".
    """
    val = (os.getenv("RATE_LIMIT_ENABLED") or "true").strip().lower()
    return val in ("1", "true", "yes", "y", "on")


def limit(rule: str) -> Callable[[F], F]:
    """
    Decorator factory that mirrors slowapi's @limiter.limit when available.

    Example:
        @limit("5/minute")
        def endpoint(...): ...

    If no limiter is configured or RATE_LIMIT_ENABLED is false,
    returns a no-op decorator.
    """
    if not _rate_limit_enabled() or _limiter is None or not hasattr(_limiter, "limit"):
        def _noop_decorator(func: F) -> F:
            @functools.wraps(func)
            def _wrapped(*args: Any, **kwargs: Any) -> Any:
                return func(*args, **kwargs)
            return _wrapped
        return _noop_decorator

    return _limiter.limit(rule)  # type: ignore[return-value]


__all__ = ["set_limiter", "get_limiter", "limit"]