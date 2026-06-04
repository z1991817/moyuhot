from __future__ import annotations

from app.models.common import APIModel


class MarketIndex(APIModel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    url: str
    market_status: str
    trade_date: str  # 交易日，格式 YYYY-MM-DD
    updated_at: str
    disclaimer: str


class MarketStock(APIModel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    url: str
    market_status: str
    trade_date: str  # 交易日，格式 YYYY-MM-DD
    updated_at: str
    disclaimer: str


class MarketResponse(APIModel):
    items: list[MarketIndex]
    stale: bool = False
    updated_at: str


class StocksResponse(APIModel):
    items: list[MarketStock]
    stale: bool = False
    updated_at: str
