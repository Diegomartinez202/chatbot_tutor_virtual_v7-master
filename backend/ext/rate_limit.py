# backend/ext/redis_client.py
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis  # type: ignore
except Exception:  # pragma: no cover
    aioredis = None  # type: ignore


# Single cached client for the process
_redis_client: Optional["aioredis.Redis"] = None


def _norm_bool(val: Optional[str], default: bool = True) -> bool:
    """
    Parse typical boolean env values. Defaults to True when unset.
    """
    if val is None:
        return default
    v = val.strip().lower()
    return v in ("1", "true", "yes", "y", "on")


def get_redis_url() -> str:
    """
    Resolve the Redis URL from environment.
    Priority:
      1) RATE_LIMIT_STORAGE_URI
      2) REDIS_URL
      3) redis://redis:6379/0 (default)
    """
    url = os.getenv("RATE_LIMIT_STORAGE_URI") or os.getenv("REDIS_URL")
    return (url or "redis://redis:6379/0").strip()


def redis_enabled() -> bool:
    """
    Decide if Redis-based features should be enabled.
    Enabled when:
      - RATE_LIMIT_BACKEND == "redis"
      - and aioredis is importable
    """
    backend = (os.getenv("RATE_LIMIT_BACKEND") or "memory").strip().lower()
    return backend == "redis" and aioredis is not None


async def get_redis() -> Optional["aioredis.Redis"]:
    """
    Return a connected Redis client or None.
    Does not raise if connection fails; it logs and returns None instead.
    """
    global _redis_client

    if not redis_enabled():
        logger.info("[redis] disabled (RATE_LIMIT_BACKEND != redis or aioredis missing)")
        return None

    if _redis_client is not None:
        # Best effort: assume still valid
        return _redis_client

    try:
        url = get_redis_url()
        _redis_client = aioredis.from_url(url, encoding="utf-8", decode_responses=True)  # type: ignore[attr-defined]
        # Light liveness check
        await _redis_client.ping()  # type: ignore[func-returns-value]
        logger.info("[redis] connected ok: %s", url)
        return _redis_client
    except Exception as e:
        logger.warning("[redis] connection failed: %s", e)
        _redis_client = None
        return None


async def close_redis() -> None:
    """
    Close the cached Redis client if present.
    """
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()  # type: ignore[attr-defined]
        except Exception:
            pass
        _redis_client = None