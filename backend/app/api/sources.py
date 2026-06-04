from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.cache.policy import as_fresh, as_stale, get_cached_response
from app.cache.sqlite import SQLiteCache
from app.clients.seesea import SeeSeaClient, SeeSeaError, get_seesea_client
from app.config import settings
from app.models.source import Source, SourcesResponse
from app.platforms import PLATFORMS
from app.source_catalog import include_known_sources

router = APIRouter(tags=["sources"])


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def get_cache(request: Request) -> SQLiteCache:
    return request.app.state.cache


@router.get("/sources", response_model=SourcesResponse)
async def list_sources(
    client: Annotated[SeeSeaClient, Depends(get_seesea_client)],
    cache: Annotated[SQLiteCache, Depends(get_cache)],
) -> SourcesResponse:
    cache_key = "sources:list"
    cached = await get_cached_response(cache, cache_key, SourcesResponse)
    if cached is not None:
        response, is_expired = cached
        if not is_expired:
            return as_fresh(response)

    try:
        now = _now_iso()
        items = await client.fetch_platforms()
        if not items:
            items = [
                Source(
                    platform=meta.platform,
                    platform_name=meta.platform_name,
                    status="ok",
                    updated_at=now,
                )
                for meta in PLATFORMS.values()
            ]
        else:
            items = include_known_sources(items, now)
        response = SourcesResponse(items=items, stale=False, updated_at=now)
        await cache.set(
            cache_key,
            response.model_dump(mode="json"),
            ttl_seconds=settings.sources_cache_ttl_seconds,
            source_status="ok",
        )
        return response
    except SeeSeaError:
        if cached is not None:
            return as_stale(cached[0])

        fallback = [
            Source(
                platform=meta.platform,
                platform_name=meta.platform_name,
                status="stale",
                updated_at=_now_iso(),
            )
            for meta in PLATFORMS.values()
        ]
        return SourcesResponse(items=fallback, stale=True, updated_at=_now_iso())
