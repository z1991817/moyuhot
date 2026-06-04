from __future__ import annotations

import argparse
import asyncio
import logging

from app.cache.sqlite import SQLiteCache
from app.clients.tdx_market import TdxMarketClient
from app.config import settings
from app.scheduler import _refresh_cn_market, cn_market_refresh_interval_seconds

logger = logging.getLogger(__name__)


async def refresh_once(*, purge: bool = False) -> int:
    cache = SQLiteCache(settings.cache_db_path)
    await cache.init()
    if purge:
        await cache.delete("market:cn")
        logger.info("cn-market-job: purged previous cn market cache")

    cn_market = TdxMarketClient()
    try:
        response = await _refresh_cn_market(cn_market, cache)
        if response is None:
            logger.warning("cn-market-job: refresh produced no cacheable data")
            return 1
        logger.info(
            "cn-market-job: refreshed (%d indices, %d stocks, stale=%s)",
            len(response.indices),
            len(response.stocks),
            response.stale,
        )
        return 0
    finally:
        await cn_market.aclose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--purge",
        action="store_true",
        help="delete the previous market:cn cache before refreshing",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(asyncio.run(refresh_once(purge=args.purge)))


async def refresh_loop() -> None:
    while True:
        try:
            await refresh_once()
        except Exception:
            logger.exception("cn-market-job: refresh crashed")
        interval = cn_market_refresh_interval_seconds()
        logger.info("cn-market-job: next refresh in %ds", interval)
        await asyncio.sleep(interval)


def loop_main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(refresh_loop())


if __name__ == "__main__":
    main()
