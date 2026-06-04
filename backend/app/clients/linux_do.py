from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx
from fastapi import Request

from app.models.trend import Trend

LINUX_DO_PLATFORM = "linux-do"
LINUX_DO_PLATFORM_NAME = "Linux.do"
LINUX_DO_HOT_FEED_URL = "https://linux.do/hot.rss"


class LinuxDoRssError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class LinuxDoRssClient:
    def __init__(
        self,
        feed_url: str = LINUX_DO_HOT_FEED_URL,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._feed_url = feed_url
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(8.0, connect=3.0),
            headers={"User-Agent": "moyu-aggregator/0.1"},
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def fetch_hot(self) -> list[Trend]:
        try:
            response = await self._client.get(self._feed_url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LinuxDoRssError("LINUX_DO_RSS_UPSTREAM", "Linux.do RSS unavailable") from exc

        return parse_linux_do_feed(response.text)


def parse_linux_do_feed(payload: str) -> list[Trend]:
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise LinuxDoRssError("LINUX_DO_RSS_PARSE", "Linux.do RSS parse failed") from exc

    channel = root.find("channel")
    entries = list(channel.findall("item")) if channel is not None else []
    now = _now_iso()
    trends: list[Trend] = []
    for rank, item in enumerate(entries, start=1):
        title = _find_text(item, "title").strip()
        url = _find_text(item, "link").strip()
        if not title or not url:
            continue
        updated_at = _parse_rss_time(_find_text(item, "pubDate")) or now
        trends.append(
            Trend(
                platform=LINUX_DO_PLATFORM,
                platform_name=LINUX_DO_PLATFORM_NAME,
                title=title,
                url=url,
                rank=rank,
                heat="HOT",
                source="linux-do-hot-rss",
                updated_at=updated_at,
            )
        )
    return trends


def _find_text(item: ElementTree.Element, name: str) -> str:
    for child in item:
        if _local_name(child.tag) == name and child.text:
            return child.text
    return ""


def _parse_rss_time(value: str) -> str | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value.strip())
    except (TypeError, ValueError):
        return value.strip()
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC).isoformat()
    return parsed.astimezone(UTC).isoformat()


def _local_name(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag[tag.index("}") + 1 :]
    return tag


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def get_linux_do_rss_client(request: Request) -> LinuxDoRssClient:
    return request.app.state.linux_do_rss_client
