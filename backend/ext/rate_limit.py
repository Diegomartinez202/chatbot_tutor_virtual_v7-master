# backend/ext/rate_limit.py
from __future__ import annotations

import logging
from typing import Any, Callable, List, Optional

from fastapi import Depends, FastAPI

# Your existing Redis helpers (expected at backend/ext/redis_client.py)
from .redis_client import get_redis, redis_enabled

# Re-export a decorator-style API from backend.rate_limit
# This allows routes to optionally do: from backend.ext.rate_limit import limit
# and use @limit("5/minute") without breaking if no real limiter is set.
try:
    from backend.rate_limit import (
        set_limiter as set_limiter,   # register a limiter object (if you use one)
        get_limiter as get_limiter,   # read current limiter (or None)
        limit as limit,               # decorator factory (no-op if not configured)
    )
except Exception:
    # Robust fallback: provide safe no-op versions if backend.rate_limit is missing
    _lim_ref: Optional[Any] = None

    def set_limiter(lim: Any) -> None:
        global _lim_ref
        _lim_ref = lim

    def get_limiter() -> Optional[Any]:
        return _lim_ref

    def limit(rule: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def _noop_decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            return fn
        return _noop_decorator

logger = logging.getLogger(__name__)


async def init_rate_limit(app: FastAPI) -> None:
    """
    Initialize FastAPILimiter only if Redis is enabled and available.
    If it fails or Redis is not enabled, the app continues without rate limiting.
    """
    try:
        from fastapi_limiter import FastAPILimiter  # local import to avoid hard dependency at import time
    except Exception:
        logger.info("[rate-limit] fastapi-limiter not installed; skipping.")
        return

    if not redis_enabled():
        logger.info("[rate-limit] Disabled (RATE_LIMIT_BACKEND != redis).")
        return

    try:
        redis = await get_redis()
        if redis is None:
            logger.warning("[rate-limit] Redis not available; skipping limiter init.")
            return
        await FastAPILimiter.init(redis)
        logger.info("[rate-limit] Enabled with Redis (fastapi-limiter).")
    except Exception as e:
        logger.warning("[rate-limit] Could not initialize: %s (skipping).", e)


def limiter(times: int = 30, seconds: int = 60) -> List[Any]:
    """
    Return a dependency list usable in FastAPI route definitions, e.g.:

        @router.post("/endpoint", dependencies=limiter(10, 60))

    If FastAPILimiter was not initialized (or missing), this returns an empty list
    so that routes keep working (no-op).
    """
    try:
        # Import here to avoid import errors at module load time.
        from fastapi_limiter import FastAPILimiter as _Check
        from fastapi_limiter.depends import RateLimiter

        # If FastAPILimiter.init(...) was not called, .redis will be None.
        if getattr(_Check, "redis", None) is None:
            return []
        return [Depends(RateLimiter(times=times, seconds=seconds))]
    except Exception:
        # If any error occurs (missing package, etc.), act as no-op.
        return []


__all__ = [
    # dependency style
    "init_rate_limit",
    "limiter",
    # decorator style re-exported from backend.rate_limit
    "set_limiter",
    "get_limiter",
    "limit",
]