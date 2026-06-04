from __future__ import annotations

import asyncio
import importlib
import math
import time as time_module
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Protocol, cast
from zoneinfo import ZoneInfo

from app.config import settings
from app.lib.china_holidays import get_china_rest_day_info
from app.models.cn_market import (
    CnActiveStock,
    CnFundFlow,
    CnMarketAnalysis,
    CnMarketBreadth,
    CnMarketIndex,
    CnMarketResponse,
    CnMarketStock,
    CnRangeStock,
    CnSectorTrend,
)

CHINA_TIME_ZONE = ZoneInfo("Asia/Shanghai")
CN_MARKET_SOURCE = "opentdx"
CN_MARKET_INCOMPLETE_REASON = "CN_MARKET_INCOMPLETE_SNAPSHOT"
CN_MARKET_REFRESH_FAILED_REASON = "CN_MARKET_REFRESH_FAILED"
CN_MARKET_NO_SNAPSHOT_REASON = "NO_CN_MARKET_SNAPSHOT"

_CN_MARKET_STOCK_LIMIT = 20
_CN_RANGE_STOCK_LIMIT = 12
_CN_ACTIVE_STOCK_LIMIT = 12
_CN_SECTOR_TREND_LIMIT = 10
_CN_MIN_INDEX_COUNT = 3
_CN_MIN_STOCK_COUNT = 10
_CN_MIN_MARKET_BREADTH_TOTAL = 1000
_CN_STOCK_SCAN_COUNT = 7000
_CN_STOCK_PAGE_SIZE = 1000
_CN_TDX_RETRY_ATTEMPTS = 3
_SINA_SECTOR_FALLBACK_URL = "https://finance.sina.com.cn/stock/sl/#sinaindustry_1"
_SINA_INDUSTRY_LABELS = {
    "交通运输": "new_jtys",
    "仪器仪表": "new_yqyb",
    "传媒娱乐": "new_cmyl",
    "供水供气": "new_gsgq",
    "公路桥梁": "new_glql",
    "其它行业": "new_qtxy",
    "农林牧渔": "new_nlmy",
    "农药化肥": "new_nyhf",
    "化工行业": "new_hghy",
    "化纤行业": "new_hqhy",
    "医疗器械": "new_ylqx",
    "印刷包装": "new_ysbz",
    "发电设备": "new_fdsb",
    "商业百货": "new_sybh",
    "塑料制品": "new_slzp",
    "家具行业": "new_jjhy",
    "家电行业": "new_jdhy",
    "建筑建材": "new_jzjc",
    "开发区": "new_kfq",
    "房地产": "new_fdc",
    "摩托车": "new_mtc",
    "有色金属": "new_ysjs",
    "服装鞋类": "new_fzxl",
    "机械行业": "new_jxhy",
    "次新股": "new_stock",
    "水泥行业": "new_snhy",
    "汽车制造": "new_qczz",
    "煤炭行业": "new_mthy",
    "物资外贸": "new_wzwm",
    "环保行业": "new_hbhy",
    "玻璃行业": "new_blhy",
    "生物制药": "new_swzz",
    "电力行业": "new_dlhy",
    "电器行业": "new_dqhy",
    "电子信息": "new_dzxx",
    "电子器件": "new_dzqj",
    "石油行业": "new_syhy",
    "纺织机械": "new_fzjx",
    "纺织行业": "new_fzhy",
    "综合行业": "new_zhhy",
    "船舶制造": "new_cbzz",
    "造纸行业": "new_zzhy",
    "酒店旅游": "new_jdly",
    "酿酒行业": "new_ljhy",
    "金融行业": "new_jrhy",
    "钢铁行业": "new_gthy",
    "陶瓷行业": "new_tchy",
    "飞机制造": "new_fjzz",
    "食品行业": "new_sphy",
}
_TDX_TO_SINA_INDUSTRY_NAME = {
    "酿酒": "酿酒行业",
    "电力": "电力行业",
    "白色家电": "家电行业",
    "一般零售": "商业百货",
}


class CnMarketError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class TdxClientProtocol(Protocol):
    def stock_quotes(self, code_list: list[tuple[object, str]]) -> object: ...

    def stock_quotes_list(
        self,
        category: object,
        start: int = 0,
        count: int = 80,
        sort_type: object | None = None,
        reverse: bool = False,
    ) -> object: ...

    def stock_board_members(self, board_symbol: object, count: int = 100000) -> object: ...

    def stock_board_list(self, market: object, count: int = 10000) -> object: ...


@dataclass(frozen=True)
class TdxRuntime:
    client_factory: Callable[[], TdxClientProtocol]
    market_sz: object
    market_sh: object
    market_bj: object
    category_a: object
    board_type_hy: object
    sort_code: object


@dataclass(frozen=True)
class TdxStockSnapshot:
    stock: CnMarketStock
    amount: float
    vol_ratio: float


class TdxMarketClient:
    def __init__(self, runtime: TdxRuntime | None = None) -> None:
        self._runtime = runtime

    async def aclose(self) -> None:
        return None

    async def fetch_cn_market(self) -> CnMarketResponse:
        try:
            return await asyncio.to_thread(self._fetch_cn_market_sync)
        except CnMarketError:
            raise
        except Exception as exc:
            raise CnMarketError(
                CN_MARKET_REFRESH_FAILED_REASON,
                "TDX A 股行情接口暂不可用",
            ) from exc

    def _fetch_cn_market_sync(self) -> CnMarketResponse:
        runtime = self._runtime or _load_tdx_runtime()
        now = datetime.now(CHINA_TIME_ZONE)
        updated_at = now.isoformat()
        data_date = _latest_trade_date(now).date().isoformat()
        market_status = _cn_market_status(now)

        client = runtime.client_factory()
        try:
            index_rows = _fetch_index_rows(client, runtime)
            board_rows = _fetch_stock_rows(client, runtime)

            indices = _map_indices(index_rows, updated_at)
            stock_snapshots = [
                snapshot
                for snapshot in (_map_stock_snapshot(row, updated_at) for row in board_rows)
                if snapshot is not None
            ]
            sector_trends = _map_sector_trends(client, runtime)
        finally:
            _close_tdx_client(client)

        stocks = sorted(
            stock_snapshots,
            key=lambda item: item.amount if item.amount > 0 else abs(item.stock.change_pct),
            reverse=True,
        )[:_CN_MARKET_STOCK_LIMIT]
        top_gainers, top_losers = _map_top_movers(stock_snapshots)
        market_breadth = _map_market_breadth(stock_snapshots)
        active_stocks = _map_active_stocks(stock_snapshots)
        response = CnMarketResponse(
            indices=indices,
            stocks=[item.stock for item in stocks],
            analysis=CnMarketAnalysis(
                market_breadth=market_breadth,
                fund_flows=[
                    CnFundFlow(
                        name=item.name,
                        value=item.value,
                        change_pct=item.change_pct,
                        direction=item.direction,
                    )
                    for item in market_breadth
                ],
                limit_up=[],
                limit_down=[],
                top_gainers=top_gainers,
                top_losers=top_losers,
                active_stocks=active_stocks,
                sector_trends=sector_trends,
            ),
            source=CN_MARKET_SOURCE,
            data_date=data_date,
            market_status=market_status,
            stale=False,
            stale_reason=None,
            updated_at=updated_at,
        )
        if not is_complete_cn_market_response(response):
            raise CnMarketError(CN_MARKET_INCOMPLETE_REASON, "TDX A 股快照不完整")
        return response


def _load_tdx_runtime() -> TdxRuntime:
    try:
        opentdx = importlib.import_module("opentdx")
        market = opentdx.MARKET
        category = opentdx.CATEGORY
        board_type = opentdx.BOARD_TYPE
        sort_type = opentdx.SORT_TYPE
    except (ImportError, AttributeError) as exc:
        raise CnMarketError(CN_MARKET_REFRESH_FAILED_REASON, "TDX A 股行情依赖不可用") from exc

    return TdxRuntime(
        client_factory=cast(Callable[[], TdxClientProtocol], opentdx.TdxClient),
        market_sz=market.SZ,
        market_sh=market.SH,
        market_bj=market.BJ,
        category_a=category.A,
        board_type_hy=board_type.HY,
        sort_code=sort_type.CODE,
    )


def is_complete_cn_market_response(response: CnMarketResponse) -> bool:
    return (
        response.source == CN_MARKET_SOURCE
        and len(response.indices) >= _CN_MIN_INDEX_COUNT
        and len(response.stocks) >= _CN_MIN_STOCK_COUNT
        and bool(response.analysis.market_breadth)
        and _market_breadth_total(response.analysis.market_breadth) >= _CN_MIN_MARKET_BREADTH_TOTAL
        and bool(response.data_date)
        and bool(response.updated_at)
    )


def mark_cn_market_stale(response: CnMarketResponse, reason: str) -> CnMarketResponse:
    return response.model_copy(update={"stale": True, "stale_reason": reason})


def empty_cn_market_response(reason: str = CN_MARKET_NO_SNAPSHOT_REASON) -> CnMarketResponse:
    now = datetime.now(CHINA_TIME_ZONE)
    return CnMarketResponse(
        indices=[],
        stocks=[],
        analysis=CnMarketAnalysis(
            market_breadth=[],
            fund_flows=[],
            limit_up=[],
            limit_down=[],
            top_gainers=[],
            top_losers=[],
            active_stocks=[],
            sector_trends=[],
        ),
        source=CN_MARKET_SOURCE,
        data_date=_latest_trade_date(now).date().isoformat(),
        market_status=_cn_market_status(now),
        stale=True,
        stale_reason=reason,
        updated_at=now.isoformat(),
    )


def _index_targets(runtime: TdxRuntime) -> list[tuple[object, str]]:
    return [
        (runtime.market_sh, "999999"),
        (runtime.market_sh, "000300"),
        (runtime.market_sh, "000905"),
        (runtime.market_sh, "000688"),
    ]


def _fetch_index_rows(client: TdxClientProtocol, runtime: TdxRuntime) -> list[dict[str, object]]:
    batch_rows = _coerce_rows(client.stock_quotes(_index_targets(runtime)))
    if batch_rows:
        return batch_rows

    rows: list[dict[str, object]] = []
    for target in _index_targets(runtime):
        target_rows: list[dict[str, object]] = []
        for attempt in range(_CN_TDX_RETRY_ATTEMPTS):
            target_rows = _coerce_rows(client.stock_quotes([target]))
            if target_rows:
                break
            _sleep_before_retry(attempt)
        rows.extend(target_rows)
    return rows


def _fetch_stock_rows(client: TdxClientProtocol, runtime: TdxRuntime) -> list[dict[str, object]]:
    best_rows: list[dict[str, object]] = []
    for attempt in range(_CN_TDX_RETRY_ATTEMPTS):
        rows = _coerce_rows(
            client.stock_board_members(runtime.category_a, count=_CN_STOCK_SCAN_COUNT)
        )
        if len(rows) > len(best_rows):
            best_rows = rows
        if len(rows) >= _CN_MIN_MARKET_BREADTH_TOTAL:
            return rows
        _sleep_before_retry(attempt)

    paged_rows = _fetch_stock_rows_by_pages(client, runtime)
    return paged_rows if len(paged_rows) > len(best_rows) else best_rows


def _fetch_stock_rows_by_pages(
    client: TdxClientProtocol,
    runtime: TdxRuntime,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for start in range(0, _CN_STOCK_SCAN_COUNT, _CN_STOCK_PAGE_SIZE):
        page = _coerce_rows(
            client.stock_quotes_list(
                runtime.category_a,
                start=start,
                count=_CN_STOCK_PAGE_SIZE,
            )
        )
        rows.extend(page)
        if len(page) < _CN_STOCK_PAGE_SIZE:
            break
    return rows


def _sleep_before_retry(attempt: int) -> None:
    if attempt < _CN_TDX_RETRY_ATTEMPTS - 1:
        time_module.sleep(0.2)


def _close_tdx_client(client: TdxClientProtocol) -> None:
    for attr_name in ("_quotation_client", "_ex_quotation_client"):
        nested = getattr(client, attr_name, None)
        if nested is None or not getattr(nested, "connected", False):
            continue
        disconnect = getattr(nested, "disconnect", None)
        if callable(disconnect):
            disconnect()


def _map_indices(rows: list[dict[str, object]], updated_at: str) -> list[CnMarketIndex]:
    meta = {
        "999999": ("000001", "上证指数"),
        "000001": ("000001", "上证指数"),
        "000300": ("000300", "沪深300"),
        "000905": ("000905", "中证500"),
        "000688": ("000688", "科创50"),
    }
    result: list[CnMarketIndex] = []
    seen: set[str] = set()
    for row in rows:
        raw_code = _normalize_symbol(_text(row, "code", "代码", "symbol"))
        symbol, name = meta.get(raw_code, (raw_code, _text(row, "name", "名称", default=raw_code)))
        if not symbol or symbol in seen:
            continue
        close = _number(row, "close", "price", "最新价")
        pre_close = _number(row, "pre_close", "昨收")
        change = _change_amount(close, pre_close)
        result.append(
            CnMarketIndex(
                symbol=symbol,
                name=name,
                price=_round_price(close),
                change=_round_price(change),
                change_pct=_change_pct(close, pre_close),
                url=_sina_index_url(symbol),
                updated_at=updated_at,
                disclaimer=settings.market_disclaimer,
            )
        )
        seen.add(symbol)
    return result


def _map_stock_snapshot(row: dict[str, object], updated_at: str) -> TdxStockSnapshot | None:
    symbol = _normalize_symbol(_text(row, "code", "代码", "symbol"))
    if not symbol:
        return None
    close = _number(row, "close", "price", "最新价")
    pre_close = _number(row, "pre_close", "昨收")
    if close <= 0:
        return None
    name = _text(row, "name", "名称", default=symbol)
    amount = _number(row, "amount", "turnover", "成交额")
    vol = _number(row, "vol", "volume", "成交量")
    stock = CnMarketStock(
        symbol=symbol,
        name=name,
        price=_round_price(close),
        change=_round_price(_change_amount(close, pre_close)),
        change_pct=_change_pct(close, pre_close),
        volume=_format_number(vol),
        turnover=_format_number(amount),
        url=_sina_stock_url(symbol),
        updated_at=updated_at,
        disclaimer=settings.market_disclaimer,
    )
    return TdxStockSnapshot(
        stock=stock,
        amount=amount,
        vol_ratio=_number(row, "vol_ratio", "volume_ratio", "量比"),
    )


def _map_top_movers(
    snapshots: list[TdxStockSnapshot],
) -> tuple[list[CnRangeStock], list[CnRangeStock]]:
    gainers = sorted(
        (item for item in snapshots if item.stock.change_pct > 0),
        key=lambda item: (item.stock.change_pct, item.amount),
        reverse=True,
    )
    losers = sorted(
        (item for item in snapshots if item.stock.change_pct < 0),
        key=lambda item: (item.stock.change_pct, -item.amount),
    )
    return (
        [_range_stock(item, "涨幅靠前") for item in gainers[:_CN_RANGE_STOCK_LIMIT]],
        [_range_stock(item, "跌幅靠前") for item in losers[:_CN_RANGE_STOCK_LIMIT]],
    )


def _range_stock(item: TdxStockSnapshot, reason: str) -> CnRangeStock:
    return CnRangeStock(
        symbol=item.stock.symbol,
        name=item.stock.name,
        price=item.stock.price,
        change_pct=item.stock.change_pct,
        reason=reason,
        url=item.stock.url,
    )


def _map_market_breadth(snapshots: list[TdxStockSnapshot]) -> list[CnMarketBreadth]:
    total = len(snapshots)
    up_count = sum(1 for item in snapshots if item.stock.change_pct > 0)
    down_count = sum(1 for item in snapshots if item.stock.change_pct < 0)
    flat_count = total - up_count - down_count
    return [
        _breadth_item("上涨家数", up_count, total, "in"),
        _breadth_item("下跌家数", down_count, total, "out"),
        _breadth_item("平盘家数", flat_count, total, "flat"),
    ]


def _map_active_stocks(snapshots: list[TdxStockSnapshot]) -> list[CnActiveStock]:
    ranked = sorted(
        snapshots,
        key=lambda item: item.vol_ratio if item.vol_ratio > 0 else item.amount,
        reverse=True,
    )
    return [
        CnActiveStock(
            symbol=item.stock.symbol,
            name=item.stock.name,
            price=item.stock.price,
            change_pct=item.stock.change_pct,
            volume=item.stock.volume,
            turnover=item.stock.turnover,
            reason=f"量比 {item.vol_ratio:.2f}" if item.vol_ratio > 0 else "成交额活跃",
            url=item.stock.url,
        )
        for item in ranked[:_CN_ACTIVE_STOCK_LIMIT]
    ]


def _map_sector_trends(client: TdxClientProtocol, runtime: TdxRuntime) -> list[CnSectorTrend]:
    try:
        rows = _coerce_rows(client.stock_board_list(runtime.board_type_hy, count=30))
    except Exception:
        return []

    trends: list[CnSectorTrend] = []
    for row in rows:
        name = _text(row, "name", "板块")
        if not name:
            continue
        price = _number(row, "price")
        pre_close = _number(row, "pre_close")
        change_pct = _change_pct(price, pre_close)
        if change_pct == 0:
            change_pct = _number(row, "rise_speed", "change_pct")
        leading_symbol = _normalize_symbol(_text(row, "symbol_code", "leading_symbol", "code"))
        leading_name = _text(row, "symbol_name", "leading_name", default=leading_symbol)
        leading_price = _number(row, "symbol_price")
        leading_pre_close = _number(row, "symbol_pre_close")
        trends.append(
            CnSectorTrend(
                name=name,
                change_pct=round(change_pct, 2),
                leading_symbol=leading_symbol,
                leading_name=leading_name,
                leading_change_pct=_change_pct(leading_price, leading_pre_close),
                url=_sina_sector_url(name),
            )
        )
    return sorted(trends, key=lambda item: item.change_pct, reverse=True)[:_CN_SECTOR_TREND_LIMIT]


def _breadth_item(name: str, count: int, total: int, direction: str) -> CnMarketBreadth:
    pct = round(count / total * 100, 2) if total else 0.0
    return CnMarketBreadth(name=name, value=str(count), change_pct=pct, direction=direction)


def _market_breadth_total(items: list[CnMarketBreadth]) -> int:
    total = 0
    for item in items:
        if item.name not in {"上涨家数", "下跌家数", "平盘家数"}:
            continue
        try:
            total += int(float(item.value.replace(",", "")))
        except ValueError:
            continue
    return total


def _coerce_rows(payload: object) -> list[dict[str, object]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("stocks", "items", "data", "result"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _text(raw: dict[str, object], *keys: str, default: str = "") -> str:
    for key in keys:
        value = raw.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def _number(raw: dict[str, object], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = raw.get(key)
        if value is None or value == "":
            continue
        try:
            numeric = float(str(value).replace(",", "").replace("%", ""))
        except ValueError:
            continue
        if math.isfinite(numeric):
            return numeric
    return default


def _normalize_symbol(symbol: str) -> str:
    value = symbol.strip()
    if "." in value:
        value = value.split(".", 1)[0]
    lower = value.lower()
    if lower.startswith(("sh", "sz", "bj")) and len(value) > 2:
        value = value[2:]
    return value.zfill(6) if value.isdigit() and len(value) < 6 else value


def _change_amount(close: float, pre_close: float) -> float:
    return close - pre_close if pre_close > 0 else 0.0


def _change_pct(close: float, pre_close: float) -> float:
    if pre_close <= 0:
        return 0.0
    return round((close - pre_close) / pre_close * 100, 2)


def _round_price(value: float) -> float:
    return round(value, 2)


def _format_number(value: float) -> str:
    if not math.isfinite(value) or value <= 0:
        return "-"
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _sina_stock_url(symbol: str) -> str:
    if not symbol:
        return "https://finance.sina.com.cn/stock/"
    if symbol.startswith(("8", "4", "9")):
        prefix = "bj"
    elif symbol.startswith(("6", "5", "7")):
        prefix = "sh"
    else:
        prefix = "sz"
    return f"https://finance.sina.com.cn/realstock/company/{prefix}{symbol}/nc.shtml"


def _sina_index_url(symbol: str) -> str:
    return f"https://finance.sina.com.cn/realstock/company/sh{symbol}/nc.shtml"


def _normalize_industry_name(name: str) -> str:
    value = name.strip()
    return _TDX_TO_SINA_INDUSTRY_NAME.get(value, value)


def _sina_sector_url(name: str) -> str:
    label = _SINA_INDUSTRY_LABELS.get(_normalize_industry_name(name))
    if not label:
        return _SINA_SECTOR_FALLBACK_URL
    return f"https://vip.stock.finance.sina.com.cn/mkt/#{label}"


def _latest_trade_date(moment: datetime) -> datetime:
    current = moment
    while get_china_rest_day_info(current).is_rest_day:
        current -= timedelta(days=1)
    return current


def _cn_market_status(moment: datetime) -> str:
    if get_china_rest_day_info(moment).is_rest_day:
        return "closed"
    current = moment.astimezone(CHINA_TIME_ZONE).time()
    if time(9, 15) <= current < time(9, 30):
        return "auction"
    if time(9, 30) <= current <= time(11, 30) or time(13, 0) <= current <= time(15, 0):
        return "trading"
    if time(11, 30) < current < time(13, 0):
        return "lunch"
    if current < time(9, 15):
        return "preopen"
    return "closed"
