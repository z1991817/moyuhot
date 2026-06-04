from __future__ import annotations

from app.models.common import APIModel


class Source(APIModel):
    platform: str
    platform_name: str
    status: str
    updated_at: str


class SourcesResponse(APIModel):
    items: list[Source]
    stale: bool = False
    updated_at: str
