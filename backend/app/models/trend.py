from __future__ import annotations

from app.models.common import APIModel


class Trend(APIModel):
    platform: str
    platform_name: str
    title: str
    url: str
    rank: int
    heat: str
    source: str
    updated_at: str


class TrendsResponse(APIModel):
    items: list[Trend]
    stale: bool = False
    updated_at: str
