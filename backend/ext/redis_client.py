# =====================================================
# backend/ext/redis_client.py
# ASCII-only, safe for Windows/Linux containers
# =====================================================
from __future__ import annotations

import os
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Optional import of redis.asyncio (do not crash if package is missing)
try:
    import redis.asyncio as aioredis  # type: ignore
except Exception:  # redis package not installed
    aioredis = None  # type: ignore

# Optional settings import (do not fail if not available)
try:
    from backend.config.settings import settings  # type: ignore
except Exception:
    settings = None  # type: ignore

# Singleton holder
_redis_client: Optional[Any] = None


def _get_backend_mode() -> str:
    """
    Returns 'redis' or 'memory' (effective backend mode).
    Priority: settings.rate_limit_backend -> env RATE_LIMIT_BACKEND -> 'memory'
    """
    if settings is not None:
        val = getattr(settings, "rate_limit_backend", None)
        if isinstance(val, str) and val.strip():
            return val.strip().lower()
    env_val = (os.getenv("RATE_LIMIT_BACKEND") or "").strip().lower()
    return env_val or "memory"


def redis_enabled() -> bool:
    """
    True if rate limit backend is 'redis' and a URL is present.
    """
    return _get_backend_mode() == "redis" and get_redis_url() is not None


def get_redis_url() -> Optional[str]:
    """
    Effective Redis URL.
    Priority: settings.redis_url -> env REDIS_URL -> default 'redis://redis:6379/0'
    """
    if settings is not None:
        url = getattr(settings, "redis_url", None)
        if isinstance(url, str) and url.strip():
            return url.strip()
    env_url = (os.getenv("REDIS_URL") or "").strip()
    if env_url:
        return env_url
    # Default to docker-compose service name 'redis'
    return "redis://redis:6379/0"


async def get_redis() -> Optional[Any]:
    """
    Returns a connected redis asyncio client or None when unavailable.
    Safe to call multiple times (singleton). Never raises on connection failure.
    """
    global _redis_client

    if not redis_enabled():
        logger.info("[redis] Disabled (backend!=redis or no URL).")
        return None

    if aioredis is None:
        logger.warning("[redis] 'redis' package not installed. Skipping.")
        return None

    if _redis_client is not None:
        return _redis_client

    url = get_redis_url()
    if not url:
        logger.warning("[redis] No URL provided. Skipping.")
        return None

    try:
        client = aioredis.from_url(url, encoding="utf-8", decode_responses=True)
        # Light ping to validate connectivity
        await client.ping()
        _redis_client = client
        logger.info("[redis] Connected to %s", url)
        return _redis_client
    except Exception as e:
        logger.warning("[redis] Connection failed: %s. Continuing without Redis.", e)
        _redis_client = None
        return None


async def close_redis() -> None:
    """
    Closes the singleton client if present.
    Compatible with redis>=4.x/5.x (aclose or close).
    """
    global _redis_client
    if _redis_client is None:
        return
    try:
        # Prefer aclose when available
        if hasattr(_redis_client, "aclose"):
            await _redis_client.aclose()
        elif hasattr(_redis_client, "close"):
            await _redis_client.close()  # type: ignore[func-returns-value]
    except Exception:
        pass
    finally:
        _redis_client = None