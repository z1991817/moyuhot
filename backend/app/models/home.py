from __future__ import annotations

from app.models.calendar import CalendarInfo
from app.models.common import APIModel
from app.models.market import MarketIndex
from app.models.source import Source
from app.models.trend import Trend


class HomeResponse(APIModel):
    trends: list[Trend]
    markets: list[MarketIndex]
    sources: list[Source]
    calendar: CalendarInfo
    stale: bool = False
    updated_at: str
