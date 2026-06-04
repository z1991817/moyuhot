from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.cache.policy import as_fresh, as_stale, get_cached_response, market_ttl_seconds
from app.cache.sqlite import SQLiteCache
from app.clients.akshare import AkShareClient, AkShareError
from app.clients.tdx_market import (
    CN_MARKET_NO_SNAPSHOT_REASON,
    empty_cn_market_response,
    is_complete_cn_market_response,
    mark_cn_market_stale,
)
from app.models.cn_market import CnMarketResponse
from app.models.market import MarketResponse, StocksResponse

router = APIRouter(tags=["market"])


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def get_cache(request: Request) -> SQLiteCache:
    return request.app.state.cache


def get_akshare_client(request: Request) -> AkShareClient:
    return request.app.state.akshare_client


def _has_real_market_values(response: MarketResponse) -> bool:
    if not response.items:
        return False
    return any(
        item.price != 0 or item.change != 0 or item.change_pct != 0 for item in response.items
    )


@router.get("/market/us", response_model=MarketResponse)
async def market_us(
    client: Annotated[AkShareClient, Depends(get_akshare_client)],
    cache: Annotated[SQLiteCache, Depends(get_cache)],
) -> MarketResponse:
    cache_key = "market:us"
    cached = await get_cached_response(cache, cache_key, MarketResponse)
    if cached is not None:
        response, is_expired = cached
        if not is_expired:
            return as_fresh(response)

    try:
        items = await client.fetch_us_indices()
        response = MarketResponse(items=items, stale=False, updated_at=_now_iso())
        if not _has_real_market_values(response):
            raise AkShareError("EMPTY_MARKET", "指数行情接口暂不可用")
        market_status = items[0].market_status if items else "closed"
        await cache.set(
            cache_key,
            response.model_dump(mode="json"),
            ttl_seconds=market_ttl_seconds(market_status),
            source_status="ok",
        )
        return response
    except AkShareError:
        if cached is not None:
            return as_stale(cached[0])
        return MarketResponse(items=[], stale=True, updated_at=_now_iso())


@router.get("/market/us/stocks", response_model=StocksResponse)
async def market_us_stocks(
    client: Annotated[AkShareClient, Depends(get_akshare_client)],
    cache: Annotated[SQLiteCache, Depends(get_cache)],
) -> StocksResponse:
    cache_key = "market:us:stocks"
    cached = await get_cached_response(cache, cache_key, StocksResponse)
    if cached is not None:
        response, is_expired = cached
        if not is_expired:
            return as_fresh(response)

    try:
        items = await client.fetch_us_stocks()
        response = StocksResponse(items=items, stale=False, updated_at=_now_iso())
        market_status = items[0].market_status if items else "closed"
        await cache.set(
            cache_key,
            response.model_dump(mode="json"),
            ttl_seconds=market_ttl_seconds(market_status),
            source_status="ok",
        )
        return response
    except AkShareError:
        if cached is not None:
            return as_stale(cached[0])
        return StocksResponse(items=[], stale=True, updated_at=_now_iso())


@router.get("/market/cn", response_model=CnMarketResponse)
async def market_cn(
    cache: Annotated[SQLiteCache, Depends(get_cache)],
) -> CnMarketResponse:
    cached = await get_cached_response(cache, "market:cn", CnMarketResponse)
    if cached is not None:
        response, is_expired = cached
        if not is_complete_cn_market_response(response):
            await cache.delete("market:cn")
            return empty_cn_market_response(CN_MARKET_NO_SNAPSHOT_REASON)
        if is_expired:
            return mark_cn_market_stale(response, "CN_MARKET_CACHE_EXPIRED")
        if response.stale:
            return mark_cn_market_stale(
                response,
                response.stale_reason or "CN_MARKET_STALE_SNAPSHOT",
            )
        return as_fresh(response)
    return empty_cn_market_response(CN_MARKET_NO_SNAPSHOT_REASON)
