from __future__ import annotations
import re, httpx, hashlib, asyncio
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Query
from backend.ext.redis_client import get_redis

router = APIRouter(prefix="/api/link", tags=["link-preview"])

ALLOWED_DOMAINS = {
    "zajuna.example", "docs.zajuna.example",
    # agrega aquí dominios que quieras habilitar
}

OG_RE = {
    "title": re.compile(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', re.I),
    "desc":  re.compile(r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']', re.I),
    "img":   re.compile(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', re.I),
}

def _hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

@router.get("/preview")
async def preview(url: str = Query(..., min_length=8, max_length=2048)):
    try:
        host = urlparse(url).hostname or ""
        if host not in ALLOWED_DOMAINS:
            raise HTTPException(status_code=400, detail="domain_not_allowed")

        rds = await get_redis()
        key = f"linkprev:{_hash(url)}"
        cached = await rds.get(key)
        if cached:
            import json
            return json.loads(cached)

        async with httpx.AsyncClient(timeout=6) as client:
            resp = await client.get(url, headers={"User-Agent": "ZajunaBot/1.0"})
            resp.raise_for_status()
            html = resp.text[:200_000]  # límite
        title = OG_RE["title"].search(html)
        desc  = OG_RE["desc"].search(html)
        img   = OG_RE["img"].search(html)

        data = {
            "url": url,
            "title": title.group(1) if title else None,
            "description": desc.group(1) if desc else None,
            "image": img.group(1) if img else None,
        }

        import json
        await rds.setex(key, 3600, json.dumps(data))  # TTL 1h
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"preview_error: {type(e).__name__}")
