# backend/ext/rate_limit.py
from __future__ import annotations
import logging
from typing import List
from fastapi import FastAPI, Depends
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from .redis_client import get_redis, redis_enabled

logger = logging.getLogger(__name__)

async def init_rate_limit(app: FastAPI) -> None:
    """
    Inicializa FastAPILimiter solo si Redis está habilitado y disponible.
    Fallback: si falla, continúa sin rate limit.
    """
    if not redis_enabled():
        logger.info("[rate-limit] Deshabilitado (RATE_LIMIT_BACKEND!=redis)")
        return
    try:
        redis = await get_redis()
        if redis is None:
            logger.warning("[rate-limit] Redis no disponible; se omite limitación.")
            return
        await FastAPILimiter.init(redis)
        logger.info("[rate-limit] Habilitado con Redis.")
    except Exception as e:
        logger.warning("[rate-limit] No se pudo inicializar: %s (se omite).", e)

def limiter(times: int = 30, seconds: int = 60):
    """
    Devuelve una lista de dependencias para usar en @router.*(dependencies=...).
    Si el limitador no está inicializado, retorna lista vacía (no rompe).
    """
    try:
        # Si FastAPILimiter no fue inicializado, RateLimiter no fallará al crear la dep,
        # pero marcaremos explícitamente el fallback retornando [].
        from fastapi_limiter import FastAPILimiter as _Check
        if getattr(_Check, "redis", None) is None:
            return []
        return [Depends(RateLimiter(times=times, seconds=seconds))]
    except Exception:
        return []