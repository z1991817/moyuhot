from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request

from app.cache.policy import as_fresh, get_cached_response, market_ttl_seconds
from app.cache.sqlite import SQLiteCache
from app.clients.akshare import AkShareClient
from app.clients.linux_do import LinuxDoRssClient, get_linux_do_rss_client
from app.clients.seesea import SeeSeaClient, get_seesea_client
from app.clients.v2ex import V2exRssClient, get_v2ex_rss_client
from app.config import settings
from app.lib.china_holidays import get_china_rest_day_info
from app.models.home import HomeResponse
from app.models.market import MarketIndex, MarketResponse
from app.models.source import Source, SourcesResponse
from app.models.trend import Trend, TrendsResponse
from app.source_catalog import include_known_sources
from app.trend_sources import fetch_trends

router = APIRouter(tags=["home"])


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def get_cache(request: Request) -> SQLiteCache:
    return request.app.state.cache


def get_akshare_client(request: Request) -> AkShareClient:
    return request.app.state.akshare_client


def get_default_platforms(request: Request) -> list[str]:
    return request.app.state.default_platforms


@router.get("/home", response_model=HomeResponse)
async def home(
    seesea_client: Annotated[SeeSeaClient, Depends(get_seesea_client)],
    v2ex_rss_client: Annotated[V2exRssClient, Depends(get_v2ex_rss_client)],
    linux_do_rss_client: Annotated[LinuxDoRssClient, Depends(get_linux_do_rss_client)],
    akshare_client: Annotated[AkShareClient, Depends(get_akshare_client)],
    cache: Annotated[SQLiteCache, Depends(get_cache)],
    default_platforms: Annotated[list[str], Depends(get_default_platforms)],
) -> HomeResponse:
    cached_home = await get_cached_response(cache, "home", HomeResponse)
    if cached_home is not None:
        response, is_expired = cached_home
        if not is_expired:
            return as_fresh(response)

    fallback_home = cached_home[0] if cached_home is not None else None

    trends_result, sources_result, markets_result = await asyncio.gather(
        fetch_trends(
            seesea_client,
            v2ex_rss_client,
            linux_do_rss_client,
            default_platforms,
        ),
        seesea_client.fetch_platforms(),
        akshare_client.fetch_us_indices(),
        return_exceptions=True,
    )

    trends_failed = isinstance(trends_result, Exception)
    sources_failed = isinstance(sources_result, Exception)
    markets_failed = isinstance(markets_result, Exception)

    trends = await _resolve_trends(
        cache,
        default_platforms,
        fallback_home,
        trends_result,
        trends_failed,
    )
    sources = await _resolve_sources(cache, fallback_home, sources_result, sources_failed)
    markets = _resolve_markets(fallback_home, markets_result, markets_failed)

    response = HomeResponse(
        trends=trends,
        markets=markets,
        sources=sources,
        calendar=get_china_rest_day_info(),
        stale=trends_failed or sources_failed or markets_failed,
        updated_at=_now_iso(),
    )

    if not response.stale:
        await _write_home_related_cache(cache, default_platforms, response)

    return response


async def _resolve_trends(
    cache: SQLiteCache,
    default_platforms: list[str],
    fallback_home: HomeResponse | None,
    result: list[Trend] | BaseException,
    failed: bool,
) -> list[Trend]:
    if not failed:
        return cast(list[Trend], result)
    if fallback_home is not None:
        return fallback_home.trends

    cache_key = f"trends:multi:{','.join(default_platforms)}"
    cached = await get_cached_response(cache, cache_key, TrendsResponse)
    return cached[0].items if cached is not None else []


async def _resolve_sources(
    cache: SQLiteCache,
    fallback_home: HomeResponse | None,
    result: list[Source] | BaseException,
    failed: bool,
) -> list[Source]:
    if not failed:
        return include_known_sources(cast(list[Source], result), _now_iso())
    if fallback_home is not None:
        return fallback_home.sources

    cached = await get_cached_response(cache, "sources:list", SourcesResponse)
    return cached[0].items if cached is not None else []


def _resolve_markets(
    fallback_home: HomeResponse | None,
    result: list[MarketIndex] | BaseException,
    failed: bool,
) -> list[MarketIndex]:
    if not failed:
        return cast(list[MarketIndex], result)
    return fallback_home.markets if fallback_home is not None else []


async def _write_home_related_cache(
    cache: SQLiteCache, default_platforms: list[str], response: HomeResponse
) -> None:
    await cache.set(
        "home",
        response.model_dump(mode="json"),
        ttl_seconds=settings.home_cache_ttl_seconds,
        source_status="ok",
    )
    await cache.set(
        f"trends:multi:{','.join(default_platforms)}",
        TrendsResponse(
            items=response.trends,
            stale=False,
            updated_at=response.updated_at,
        ).model_dump(mode="json"),
        ttl_seconds=settings.trends_cache_ttl_seconds,
        source_status="ok",
    )
    await cache.set(
        "sources:list",
        SourcesResponse(
            items=response.sources,
            stale=False,
            updated_at=response.updated_at,
        ).model_dump(mode="json"),
        ttl_seconds=settings.sources_cache_ttl_seconds,
        source_status="ok",
    )

    market_status = response.markets[0].market_status if response.markets else "closed"
    await cache.set(
        "market:us",
        MarketResponse(
            items=response.markets,
            stale=False,
            updated_at=response.updated_at,
        ).model_dump(mode="json"),
        ttl_seconds=market_ttl_seconds(market_status),
        source_status="ok",
    )
