# backend/ext/rate_limit.py
from __future__ import annotations

import logging
from typing import Optional, List
from fastapi import FastAPI, Depends

# Try to use fastapi-limiter if available; otherwise fall back to no-op
try:
    from fastapi_limiter import FastAPILimiter  # type: ignore
    from fastapi_limiter.depends import RateLimiter  # type: ignore
    _HAS_FASTAPI_LIMITER = True
except Exception:  # pragma: no cover
    FastAPILimiter = None  # type: ignore
    RateLimiter = None  # type: ignore
    _HAS_FASTAPI_LIMITER = False

from .redis_client import get_redis, redis_enabled

logger = logging.getLogger(__name__)

async def init_rate_limit(app: FastAPI) -> None:
    """
    Initialize fastapi-limiter only if Redis is enabled and available.
    If initialization fails, continue without rate limiting (no exceptions).
    """
    if not _HAS_FASTAPI_LIMITER:
        logger.info("[rate-limit] fastapi-limiter not installed; skipping.")
        return

    if not redis_enabled():
        logger.info("[rate-limit] disabled (RATE_LIMIT_BACKEND != 'redis').")
        return

    try:
        redis = await get_redis()
        if redis is None:
            logger.warning("[rate-limit] Redis not available; skipping limiter.")
            return
        await FastAPILimiter.init(redis)  # type: ignore[attr-defined]
        logger.info("[rate-limit] initialized with Redis backend.")
    except Exception as exc:
        logger.warning("[rate-limit] initialization failed: %s (limiter disabled)", exc)

def limiter(times: int = 30, seconds: int = 60) -> List:
    """
    Returns a list with a RateLimiter dependency when available; otherwise [].
    Usage in routes:
        @router.post("/chat", dependencies=limiter(30, 60))
    """
    if not _HAS_FASTAPI_LIMITER:
        return []

    try:
        # If FastAPILimiter.init() wasn't called (no redis), don't attach a dead dep
        if getattr(FastAPILimiter, "redis", None) is None:  # type: ignore[attr-defined]
            return []
        return [Depends(RateLimiter(times=times, seconds=seconds))]  # type: ignore[misc]
    except Exception as exc:
        logger.debug("[rate-limit] fallback to no-op: %s", exc)
        return []

__all__ = ["init_rate_limit", "limiter"]
