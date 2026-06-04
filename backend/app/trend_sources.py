from __future__ import annotations

import asyncio

from app.clients.linux_do import LINUX_DO_PLATFORM, LinuxDoRssClient
from app.clients.seesea import SeeSeaClient
from app.clients.v2ex import V2EX_PLATFORM, V2exRssClient
from app.models.trend import Trend


async def fetch_trends(
    seesea_client: SeeSeaClient,
    v2ex_rss_client: V2exRssClient,
    linux_do_rss_client: LinuxDoRssClient,
    platforms: list[str],
) -> list[Trend]:
    external_rss_platforms = {V2EX_PLATFORM, LINUX_DO_PLATFORM}
    seesea_platforms = [
        platform for platform in platforms if platform not in external_rss_platforms
    ]
    include_v2ex = V2EX_PLATFORM in platforms
    include_linux_do = LINUX_DO_PLATFORM in platforms

    tasks = []
    if seesea_platforms:
        tasks.append(seesea_client.fetch_multiple(seesea_platforms))
    if include_v2ex:
        tasks.append(v2ex_rss_client.fetch_index())
    if include_linux_do:
        tasks.append(linux_do_rss_client.fetch_hot())

    results = await asyncio.gather(*tasks) if tasks else []
    seesea_items = results[0] if seesea_platforms else []
    v2ex_index = 1 if seesea_platforms else 0
    v2ex_items = results[v2ex_index] if include_v2ex else []
    linux_do_index = int(bool(seesea_platforms)) + int(include_v2ex)
    linux_do_items = results[linux_do_index] if include_linux_do else []

    return _order_by_platform([*seesea_items, *v2ex_items, *linux_do_items], platforms)


def _order_by_platform(items: list[Trend], platforms: list[str]) -> list[Trend]:
    by_platform: dict[str, list[Trend]] = {}
    for item in items:
        by_platform.setdefault(item.platform, []).append(item)

    ordered: list[Trend] = []
    seen: set[str] = set()
    for platform in platforms:
        if platform in seen:
            continue
        seen.add(platform)
        ordered.extend(by_platform.pop(platform, []))

    for rest in by_platform.values():
        ordered.extend(rest)
    return ordered
