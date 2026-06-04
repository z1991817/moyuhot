from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime, time
from typing import Protocol
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from app.cache.policy import market_ttl_seconds
from app.cache.sqlite import SQLiteCache
from app.clients.akshare import AkShareClient, AkShareError
from app.clients.linux_do import LinuxDoRssClient, LinuxDoRssError
from app.clients.seesea import SeeSeaClient, SeeSeaError
from app.clients.tdx_market import (
    CN_MARKET_INCOMPLETE_REASON,
    CN_MARKET_REFRESH_FAILED_REASON,
    CnMarketError,
    TdxMarketClient,
    is_complete_cn_market_response,
    mark_cn_market_stale,
)
from app.clients.v2ex import V2exRssClient, V2exRssError
from app.config import settings
from app.lib.china_holidays import get_china_rest_day_info
from app.models.cn_market import CnMarketResponse
from app.models.home import HomeResponse
from app.models.market import MarketResponse, StocksResponse
from app.models.source import Source, SourcesResponse
from app.models.trend import TrendsResponse
from app.platforms import PLATFORMS
from app.source_catalog import include_known_sources
from app.trend_sources import fetch_trends

logger = logging.getLogger(__name__)

INITIAL_REFRESH_DELAY_SECONDS = 10
CN_MARKET_REFRESH_TIMEOUT_SECONDS = 120
CHINA_TIME_ZONE = ZoneInfo("Asia/Shanghai")


class CnMarketFetcher(Protocol):
    async def fetch_cn_market(self) -> CnMarketResponse: ...


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _market_open() -> bool:
    """美东夏令时 UTC-4: 开盘 13:30，收盘 20:00。"""
    t = datetime.now(UTC).time()
    return time(13, 30) <= t <= time(20, 0)


def _refresh_interval() -> int:
    """交易时段 3 分钟，非交易时段 30 分钟。"""
    return 180 if _market_open() else 1800


def _cn_market_open(moment: datetime | None = None) -> bool:
    if moment is None:
        moment = datetime.now(UTC)

    china_moment = moment.astimezone(CHINA_TIME_ZONE)
    if get_china_rest_day_info(china_moment).is_rest_day:
        return False

    current_time = china_moment.time()
    return time(9, 30) <= current_time <= time(11, 30) or time(13, 0) <= current_time <= time(15, 0)


def cn_market_refresh_interval_seconds(moment: datetime | None = None) -> int:
    """A 股交易时段 3 分钟，非交易时段 30 分钟。"""
    return 180 if _cn_market_open(moment) else 1800


def _cn_market_status(moment: datetime | None = None) -> str:
    return "open" if _cn_market_open(moment) else "closed"


async def _refresh_trends(
    seesea: SeeSeaClient,
    v2ex_rss: V2exRssClient,
    linux_do_rss: LinuxDoRssClient,
    cache: SQLiteCache,
    default_platforms: list[str],
) -> TrendsResponse | None:
    cache_key = f"trends:multi:{','.join(default_platforms)}"
    try:
        items = await fetch_trends(seesea, v2ex_rss, linux_do_rss, default_platforms)
        response = TrendsResponse(items=items, stale=False, updated_at=_now_iso())
        await cache.set(
            cache_key,
            response.model_dump(mode="json"),
            ttl_seconds=settings.trends_cache_ttl_seconds,
            source_status="ok",
        )
        logger.info("scheduler: trends refreshed (%d items)", len(items))
        return response
    except (SeeSeaError, V2exRssError, LinuxDoRssError) as e:
        logger.warning("scheduler: trends refresh failed: %s", e)
        return None


async def _refresh_sources(
    seesea: SeeSeaClient,
    cache: SQLiteCache,
) -> SourcesResponse | None:
    try:
        now = _now_iso()
        items = await seesea.fetch_platforms()
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
            "sources:list",
            response.model_dump(mode="json"),
            ttl_seconds=settings.sources_cache_ttl_seconds,
            source_status="ok",
        )
        logger.info("scheduler: sources refreshed (%d items)", len(items))
        return response
    except SeeSeaError as e:
        logger.warning("scheduler: sources refresh failed: %s", e)
        return None


async def _refresh_market(
    akshare: AkShareClient,
    cache: SQLiteCache,
) -> MarketResponse | None:
    try:
        items = await akshare.fetch_us_indices()
        response = MarketResponse(items=items, stale=False, updated_at=_now_iso())
        market_status = items[0].market_status if items else "closed"
        await cache.set(
            "market:us",
            response.model_dump(mode="json"),
            ttl_seconds=market_ttl_seconds(market_status),
            source_status="ok",
        )
        logger.info("scheduler: market indices refreshed (%d items)", len(items))
        return response
    except AkShareError as e:
        logger.warning("scheduler: market refresh failed: %s", e)
        return None


async def _refresh_stocks(
    akshare: AkShareClient,
    cache: SQLiteCache,
) -> StocksResponse | None:
    try:
        items = await akshare.fetch_us_stocks()
        response = StocksResponse(items=items, stale=False, updated_at=_now_iso())
        market_status = items[0].market_status if items else "closed"
        await cache.set(
            "market:us:stocks",
            response.model_dump(mode="json"),
            ttl_seconds=market_ttl_seconds(market_status),
            source_status="ok",
        )
        logger.info("scheduler: hot stocks refreshed (%d items)", len(items))
        return response
    except AkShareError as e:
        logger.warning("scheduler: stocks refresh failed: %s", e)
        return None


async def _refresh_cn_market(
    cn_market: CnMarketFetcher,
    cache: SQLiteCache,
) -> CnMarketResponse | None:
    stale_reason = CN_MARKET_REFRESH_FAILED_REASON
    try:
        response = await asyncio.wait_for(
            cn_market.fetch_cn_market(),
            timeout=CN_MARKET_REFRESH_TIMEOUT_SECONDS,
        )
        if not is_complete_cn_market_response(response):
            raise CnMarketError(CN_MARKET_INCOMPLETE_REASON, "TDX A 股快照不完整")
        response = response.model_copy(update={"stale": False, "stale_reason": None})
        await cache.set(
            "market:cn",
            response.model_dump(mode="json"),
            ttl_seconds=market_ttl_seconds(_cn_market_status()),
            source_status="ok",
        )
        logger.info(
            "scheduler: cn market refreshed (%d indices, %d stocks)",
            len(response.indices),
            len(response.stocks),
        )
        return response
    except CnMarketError as e:
        stale_reason = e.code
        logger.warning("scheduler: cn market refresh failed: %s", e)
    except TimeoutError:
        stale_reason = "CN_MARKET_REFRESH_TIMEOUT"
        logger.warning("scheduler: cn market refresh timed out")

    return await _mark_cached_cn_market_stale(cache, stale_reason)


async def _mark_cached_cn_market_stale(
    cache: SQLiteCache,
    stale_reason: str,
) -> CnMarketResponse | None:
    cached = await cache.get("market:cn")
    if cached is None:
        return None

    payload, _is_expired = cached
    try:
        cached_response = CnMarketResponse.model_validate(payload)
    except ValidationError:
        return None
    if not is_complete_cn_market_response(cached_response):
        return None

    stale_response = mark_cn_market_stale(cached_response, stale_reason)
    await cache.set(
        "market:cn",
        stale_response.model_dump(mode="json"),
        ttl_seconds=market_ttl_seconds("closed"),
        source_status="stale",
    )
    logger.info(
        "scheduler: cn market kept previous complete snapshot (%s)",
        stale_reason,
    )
    return stale_response


async def _refresh_all(
    seesea: SeeSeaClient,
    v2ex_rss: V2exRssClient,
    linux_do_rss: LinuxDoRssClient,
    akshare: AkShareClient,
    cn_market: TdxMarketClient,
    cache: SQLiteCache,
    default_platforms: list[str],
) -> None:
    refresh_tasks = [
        _refresh_trends(seesea, v2ex_rss, linux_do_rss, cache, default_platforms),
        _refresh_sources(seesea, cache),
        _refresh_market(akshare, cache),
        _refresh_stocks(akshare, cache),
    ]
    if settings.cn_market_scheduler_enabled:
        refresh_tasks.append(_refresh_cn_market(cn_market, cache))

    results = await asyncio.gather(*refresh_tasks, return_exceptions=True)
    trends_result = results[0]
    sources_result = results[1]
    market_result = results[2]

    if (
        isinstance(trends_result, TrendsResponse)
        and isinstance(sources_result, SourcesResponse)
        and isinstance(market_result, MarketResponse)
    ):
        response = HomeResponse(
            trends=trends_result.items,
            sources=sources_result.items,
            markets=market_result.items,
            calendar=get_china_rest_day_info(),
            stale=False,
            updated_at=_now_iso(),
        )
        await cache.set(
            "home",
            response.model_dump(mode="json"),
            ttl_seconds=settings.home_cache_ttl_seconds,
            source_status="ok",
        )
        logger.info("scheduler: home refreshed")


async def run_refresh_loop(app) -> None:  # type: ignore[no-untyped-def]
    cache: SQLiteCache = app.state.cache
    seesea: SeeSeaClient = app.state.seesea_client
    v2ex_rss: V2exRssClient = app.state.v2ex_rss_client
    linux_do_rss: LinuxDoRssClient = app.state.linux_do_rss_client
    akshare: AkShareClient = app.state.akshare_client
    cn_market: TdxMarketClient = app.state.cn_market_client
    default_platforms: list[str] = app.state.default_platforms

    await asyncio.sleep(INITIAL_REFRESH_DELAY_SECONDS)
    await _refresh_all(seesea, v2ex_rss, linux_do_rss, akshare, cn_market, cache, default_platforms)

    while True:
        interval = _refresh_interval()
        logger.info(
            "scheduler: next refresh in %ds (market %s)",
            interval,
            "open" if _market_open() else "closed",
        )
        await asyncio.sleep(interval)

        await _refresh_all(
            seesea, v2ex_rss, linux_do_rss, akshare, cn_market, cache, default_platforms
        )


def start_scheduler(app) -> asyncio.Task[None]:  # type: ignore[no-untyped-def]
    return asyncio.create_task(run_refresh_loop(app))


async def stop_scheduler(task: asyncio.Task[None]) -> None:
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
