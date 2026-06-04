from __future__ import annotations

from app.models.source import Source
from app.platforms import PLATFORMS


def include_known_sources(
    items: list[Source], updated_at: str, *, status: str = "ok"
) -> list[Source]:
    by_platform = {item.platform: item for item in items}
    for meta in PLATFORMS.values():
        by_platform.setdefault(
            meta.platform,
            Source(
                platform=meta.platform,
                platform_name=meta.platform_name,
                status=status,
                updated_at=updated_at,
            ),
        )
    return list(by_platform.values())
