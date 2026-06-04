from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.cache.policy import as_fresh, as_stale, get_cached_response
from app.cache.sqlite import SQLiteCache
from app.clients.linux_do import LinuxDoRssClient, LinuxDoRssError, get_linux_do_rss_client
from app.clients.seesea import SeeSeaClient, SeeSeaError, get_seesea_client
from app.clients.v2ex import V2exRssClient, V2exRssError, get_v2ex_rss_client
from app.config import settings
from app.models.trend import TrendsResponse
from app.platforms import normalize_platforms
from app.trend_sources import fetch_trends

router = APIRouter(tags=["trends"])


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def get_cache(request: Request) -> SQLiteCache:
    return request.app.state.cache


@router.get("/trends", response_model=TrendsResponse)
async def list_trends(
    client: Annotated[SeeSeaClient, Depends(get_seesea_client)],
    v2ex_rss_client: Annotated[V2exRssClient, Depends(get_v2ex_rss_client)],
    linux_do_rss_client: Annotated[LinuxDoRssClient, Depends(get_linux_do_rss_client)],
    cache: Annotated[SQLiteCache, Depends(get_cache)],
    platform: str | None = None,
    refresh: bool = False,
) -> TrendsResponse:
    platforms = normalize_platforms(platform)
    cache_key = f"trends:multi:{','.join(platforms)}"
    cached = await get_cached_response(cache, cache_key, TrendsResponse)
    if not refresh and cached is not None:
        response, is_expired = cached
        if not is_expired:
            return as_fresh(response)

    try:
        items = await fetch_trends(client, v2ex_rss_client, linux_do_rss_client, platforms)
        response = TrendsResponse(items=items, stale=False, updated_at=_now_iso())
        await cache.set(
            cache_key,
            response.model_dump(mode="json"),
            ttl_seconds=settings.trends_cache_ttl_seconds,
            source_status="ok",
        )
        return response
    except (SeeSeaError, V2exRssError, LinuxDoRssError):
        if cached is not None:
            return as_stale(cached[0])
        return TrendsResponse(items=[], stale=True, updated_at=_now_iso())
