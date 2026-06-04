from __future__ import annotations

from pydantic import Field, model_validator

from app.models.common import APIModel


class CnMarketIndex(APIModel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    url: str
    updated_at: str
    disclaimer: str


class CnMarketStock(APIModel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    volume: str
    turnover: str
    url: str
    updated_at: str
    disclaimer: str


class CnMarketBreadth(APIModel):
    name: str
    value: str
    change_pct: float
    direction: str


class CnFundFlow(CnMarketBreadth):
    pass


class CnLimitStock(APIModel):
    symbol: str
    name: str
    price: float
    change_pct: float
    reason: str
    url: str


class CnRangeStock(APIModel):
    symbol: str
    name: str
    price: float
    change_pct: float
    reason: str
    url: str


class CnActiveStock(APIModel):
    symbol: str
    name: str
    price: float
    change_pct: float
    volume: str
    turnover: str
    reason: str
    url: str


class CnSectorTrend(APIModel):
    name: str
    change_pct: float
    leading_symbol: str
    leading_name: str
    leading_change_pct: float
    url: str


class CnMarketAnalysis(APIModel):
    market_breadth: list[CnMarketBreadth] = Field(default_factory=list)
    fund_flows: list[CnFundFlow] = Field(default_factory=list)
    limit_up: list[CnLimitStock] = Field(default_factory=list)
    limit_down: list[CnLimitStock] = Field(default_factory=list)
    top_gainers: list[CnRangeStock] = Field(default_factory=list)
    top_losers: list[CnRangeStock] = Field(default_factory=list)
    active_stocks: list[CnActiveStock] = Field(default_factory=list)
    sector_trends: list[CnSectorTrend] = Field(default_factory=list)

    @model_validator(mode="after")
    def sync_legacy_breadth_alias(self) -> CnMarketAnalysis:
        if self.market_breadth and not self.fund_flows:
            self.fund_flows = [
                CnFundFlow(
                    name=item.name,
                    value=item.value,
                    change_pct=item.change_pct,
                    direction=item.direction,
                )
                for item in self.market_breadth
            ]
        elif self.fund_flows and not self.market_breadth:
            self.market_breadth = [
                CnMarketBreadth(
                    name=item.name,
                    value=item.value,
                    change_pct=item.change_pct,
                    direction=item.direction,
                )
                for item in self.fund_flows
            ]
        return self


class CnMarketResponse(APIModel):
    indices: list[CnMarketIndex]
    stocks: list[CnMarketStock]
    analysis: CnMarketAnalysis
    source: str = ""
    data_date: str = ""
    market_status: str = ""
    stale: bool = False
    stale_reason: str | None = None
    updated_at: str
