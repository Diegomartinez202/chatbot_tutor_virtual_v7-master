# backend/ext/redis_client.py
from __future__ import annotations
import os
import logging
from typing import Optional
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_redis: Optional[Redis] = None

def redis_enabled() -> bool:
    return (os.getenv("RATE_LIMIT_BACKEND") or "").lower() == "redis"

def get_redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://redis:6379/0")

async def get_redis() -> Optional[Redis]:
    """
    Devuelve un cliente Redis asyncio o None si no está habilitado.
    No lanza excepciones: si falla, loggea y retorna None (fallback seguro).
    """
    global _redis
    if not redis_enabled():
        return None
    if _redis is None:
        try:
            _redis = Redis.from_url(get_redis_url(), encoding="utf-8", decode_responses=True)
            # ping ligero para validar conexión (no rompe si falla)
            await _redis.ping()
            logger.info("[redis] Conectado a %s", get_redis_url())
        except Exception as e:
            logger.warning("[redis] No se pudo conectar (%s). Continuando sin Redis.", e)
            _redis = None
    return _redis

async def close_redis() -> None:
    global _redis
    if _redis is not None:
        try:
            await _redis.close()
        except Exception:
            pass
        _redis = None