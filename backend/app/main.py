from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    chat_router,
    health_router,
    home_router,
    market_router,
    sources_router,
    trends_router,
)
from app.cache.sqlite import SQLiteCache
from app.clients.akshare import AkShareClient
from app.clients.chat_gateway import ChatGatewayClient
from app.clients.linux_do import LinuxDoRssClient
from app.clients.seesea import SeeSeaClient
from app.clients.tdx_market import TdxMarketClient
from app.clients.v2ex import V2exRssClient
from app.config import settings
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache = SQLiteCache(settings.cache_db_path)
    await cache.init()

    app.state.cache = cache
    app.state.seesea_client = SeeSeaClient()
    app.state.v2ex_rss_client = V2exRssClient()
    app.state.linux_do_rss_client = LinuxDoRssClient()
    app.state.akshare_client = AkShareClient()
    app.state.cn_market_client = TdxMarketClient()
    app.state.chat_gateway_client = ChatGatewayClient()
    app.state.default_platforms = settings.seesea_default_platforms

    scheduler_task = start_scheduler(app)
    try:
        yield
    finally:
        await stop_scheduler(scheduler_task)
        await app.state.seesea_client.aclose()
        await app.state.v2ex_rss_client.aclose()
        await app.state.linux_do_rss_client.aclose()
        await app.state.akshare_client.aclose()
        await app.state.cn_market_client.aclose()
        await app.state.chat_gateway_client.aclose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(home_router, prefix=settings.api_prefix)
app.include_router(trends_router, prefix=settings.api_prefix)
app.include_router(sources_router, prefix=settings.api_prefix)
app.include_router(market_router, prefix=settings.api_prefix)
app.include_router(chat_router, prefix=settings.api_prefix)
app.include_router(health_router)
