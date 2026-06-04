from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime, time

import httpx

from app.config import settings
from app.models.market import MarketIndex, MarketStock


class AkShareError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_SINA_QUOTE_BASE = "https://stock.finance.sina.com.cn/usstock/quotes"

_SINA_SYMBOLS: list[tuple[str, str, str, str]] = [
    ("SPX", "S&P 500", "gb_$inx", ".INX"),
    ("DJI", "Dow Jones", "gb_$dji", ".DJI"),
    ("IXIC", "Nasdaq Composite", "gb_$ixic", ".IXIC"),
    ("NDX", "Nasdaq 100", "gb_$ndx", ".NDX"),
]

_TENCENT_SYMBOLS: list[tuple[str, str, str, str]] = [
    ("VIX", "VIX", "usVIX", ".VIX"),
]

# 热门美股个股（新浪代码 gb_xxx）
_STOCK_SYMBOLS: list[tuple[str, str, str]] = [
    ("AAPL", "苹果", "gb_aapl"),
    ("NVDA", "英伟达", "gb_nvda"),
    ("MSFT", "微软", "gb_msft"),
    ("AMZN", "亚马逊", "gb_amzn"),
    ("GOOGL", "谷歌", "gb_googl"),
    ("META", "Meta", "gb_meta"),
    ("TSLA", "特斯拉", "gb_tsla"),
    ("NFLX", "奈飞", "gb_nflx"),
    ("AMD", "AMD", "gb_amd"),
    ("BABA", "阿里巴巴", "gb_baba"),
]

_SINA_URL = "https://hq.sinajs.cn/list=" + ",".join(s[2] for s in _SINA_SYMBOLS)
_TENCENT_URL = "https://qt.gtimg.cn/q=" + ",".join(s[2] for s in _TENCENT_SYMBOLS)
_STOCKS_URL = "https://hq.sinajs.cn/list=" + ",".join(s[2] for s in _STOCK_SYMBOLS)

# 新浪字段顺序: 名称,当前价,涨跌幅%,时间(YYYY-MM-DD HH:MM:SS),涨跌额,...
_SINA_F_PRICE = 1
_SINA_F_PCT = 2
_SINA_F_TIME = 3
_SINA_F_CHANGE = 4

# 腾讯字段顺序(~分隔): 0=状态码,1=名称,2=代码,3=当前价,...,31=时间,32=涨跌额,33=涨跌幅%
_TX_F_PRICE = 3
_TX_F_TIME = 31
_TX_F_CHANGE = 32
_TX_F_PCT = 33


class AkShareClient:
    def __init__(self) -> None:
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def fetch_us_indices(self) -> list[MarketIndex]:
        status = _market_status()
        try:
            sina_resp, tx_resp = await _fetch_both(self._http)
            result = _parse_sina(sina_resp, status)
            result += _parse_tencent(tx_resp, status)
            if not result:
                raise AkShareError("EMPTY", "未解析到任何指数数据")
            return result
        except AkShareError:
            raise
        except Exception as exc:
            raise AkShareError("MARKET_UPSTREAM", "指数行情接口暂不可用") from exc

    async def fetch_us_stocks(self) -> list[MarketStock]:
        status = _market_status()
        try:
            resp = await self._http.get(
                _STOCKS_URL, headers={"Referer": "https://finance.sina.com.cn"}
            )
            resp.raise_for_status()
            text = resp.content.decode("gbk", errors="replace")
            return _parse_sina_stocks(text, status)
        except AkShareError:
            raise
        except Exception as exc:
            raise AkShareError("STOCKS_UPSTREAM", "个股行情接口暂不可用") from exc

    def _fallback_indices(self, status: str) -> list[MarketIndex]:
        return _fallback_indices(status)


async def _fetch_both(client: httpx.AsyncClient) -> tuple[str, str]:
    sina_task = client.get(_SINA_URL, headers={"Referer": "https://finance.sina.com.cn"})
    tx_task = client.get(_TENCENT_URL, headers={"Referer": "https://finance.qq.com"})
    sina_r, tx_r = await asyncio.gather(sina_task, tx_task, return_exceptions=True)
    return _decode_response(sina_r), _decode_response(tx_r)


def _decode_response(result: httpx.Response | BaseException) -> str:
    if isinstance(result, BaseException):
        return ""
    return result.content.decode("gbk", errors="replace")


def _fallback_indices(status: str) -> list[MarketIndex]:
    now = datetime.now(UTC).isoformat()
    trade_date = now[:10]
    symbols = _SINA_SYMBOLS + _TENCENT_SYMBOLS
    return [
        MarketIndex(
            symbol=symbol,
            name=name,
            price=0.0,
            change=0.0,
            change_pct=0.0,
            url=_sina_quote_url(quote_symbol),
            market_status=status,
            trade_date=trade_date,
            updated_at=now,
            disclaimer=settings.market_disclaimer,
        )
        for symbol, name, _, quote_symbol in symbols
    ]


def _parse_sina(text: str, status: str) -> list[MarketIndex]:
    now = datetime.now(UTC).isoformat()
    result: list[MarketIndex] = []
    for symbol, name, sina_key, quote_symbol in _SINA_SYMBOLS:
        pattern = rf'hq_str_{re.escape(sina_key)}="([^"]+)"'
        m = re.search(pattern, text)
        if not m:
            continue
        fields = m.group(1).split(",")
        if len(fields) <= _SINA_F_CHANGE:
            continue
        try:
            price = float(fields[_SINA_F_PRICE])
            change_pct = float(fields[_SINA_F_PCT])
            change = float(fields[_SINA_F_CHANGE])
        except (ValueError, IndexError):
            continue
        trade_date = fields[_SINA_F_TIME][:10] if len(fields) > _SINA_F_TIME else ""
        result.append(
            MarketIndex(
                symbol=symbol,
                name=name,
                price=round(price, 2),
                change=round(change, 2),
                change_pct=round(change_pct, 2),
                url=_sina_quote_url(quote_symbol),
                market_status=status,
                trade_date=trade_date,
                updated_at=now,
                disclaimer=settings.market_disclaimer,
            )
        )
    return result


def _parse_tencent(text: str, status: str) -> list[MarketIndex]:
    now = datetime.now(UTC).isoformat()
    result: list[MarketIndex] = []
    for symbol, name, tx_key, quote_symbol in _TENCENT_SYMBOLS:
        pattern = rf'v_{re.escape(tx_key)}="([^"]+)"'
        m = re.search(pattern, text)
        if not m:
            continue
        fields = m.group(1).split("~")
        if len(fields) <= max(_TX_F_PRICE, _TX_F_CHANGE, _TX_F_PCT):
            continue
        try:
            price = float(fields[_TX_F_PRICE])
            change = float(fields[_TX_F_CHANGE]) if fields[_TX_F_CHANGE] else 0.0
            change_pct = float(fields[_TX_F_PCT]) if fields[_TX_F_PCT] else 0.0
        except (ValueError, IndexError):
            continue
        raw_time = fields[_TX_F_TIME] if len(fields) > _TX_F_TIME else ""
        trade_date = raw_time[:10] if raw_time else ""
        result.append(
            MarketIndex(
                symbol=symbol,
                name=name,
                price=round(price, 2),
                change=round(change, 2),
                change_pct=round(change_pct, 2),
                url=_sina_quote_url(quote_symbol),
                market_status=status,
                trade_date=trade_date,
                updated_at=now,
                disclaimer=settings.market_disclaimer,
            )
        )
    return result


def _parse_sina_stocks(text: str, status: str) -> list[MarketStock]:
    now = datetime.now(UTC).isoformat()
    result: list[MarketStock] = []
    for symbol, cn_name, sina_key in _STOCK_SYMBOLS:
        pattern = rf'hq_str_{re.escape(sina_key)}="([^"]+)"'
        m = re.search(pattern, text)
        if not m:
            continue
        fields = m.group(1).split(",")
        if len(fields) <= _SINA_F_CHANGE:
            continue
        try:
            price = float(fields[_SINA_F_PRICE])
            change_pct = float(fields[_SINA_F_PCT])
            change = float(fields[_SINA_F_CHANGE])
        except (ValueError, IndexError):
            continue
        trade_date = fields[_SINA_F_TIME][:10] if len(fields) > _SINA_F_TIME else ""
        url = _sina_quote_url(symbol)
        result.append(
            MarketStock(
                symbol=symbol,
                name=cn_name,
                price=round(price, 2),
                change=round(change, 2),
                change_pct=round(change_pct, 2),
                url=url,
                market_status=status,
                trade_date=trade_date,
                updated_at=now,
                disclaimer=settings.market_disclaimer,
            )
        )
    return result


def _market_status() -> str:
    now = datetime.now(UTC)
    # 美东夏令时 UTC-4: 开盘 13:30 UTC，收盘 20:00 UTC
    if time(13, 30) <= now.time() <= time(20, 0):
        return "open"
    return "closed"


def _sina_quote_url(symbol: str) -> str:
    return f"{_SINA_QUOTE_BASE}/{symbol}.html"
