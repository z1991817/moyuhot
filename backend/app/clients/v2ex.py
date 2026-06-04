from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx
from fastapi import Request

from app.models.trend import Trend

V2EX_PLATFORM = "v2ex"
V2EX_PLATFORM_NAME = "V2EX"
V2EX_INDEX_FEED_URL = "https://v2ex.com/index.xml"


class V2exRssError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class V2exRssClient:
    def __init__(
        self,
        feed_url: str = V2EX_INDEX_FEED_URL,
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

    async def fetch_index(self) -> list[Trend]:
        try:
            response = await self._client.get(self._feed_url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise V2exRssError("V2EX_RSS_UPSTREAM", "V2EX RSS 暂不可用") from exc

        return parse_v2ex_feed(response.text)


def parse_v2ex_feed(payload: str) -> list[Trend]:
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise V2exRssError("V2EX_RSS_PARSE", "V2EX RSS 解析失败") from exc

    entries = _rss_items(root)
    if not entries:
        entries = _atom_entries(root)

    now = _now_iso()
    trends: list[Trend] = []
    for rank, item in enumerate(entries, start=1):
        title = _entry_title(item)
        url = _entry_url(item)
        if not title or not url:
            continue
        updated_at = _entry_time(item) or now
        trends.append(
            Trend(
                platform=V2EX_PLATFORM,
                platform_name=V2EX_PLATFORM_NAME,
                title=title,
                url=url,
                rank=rank,
                heat="RSS",
                source="v2ex-index-rss",
                updated_at=updated_at,
            )
        )
    return trends


def _rss_items(root: ElementTree.Element) -> list[ElementTree.Element]:
    channel = root.find("channel")
    if channel is None:
        return []
    return list(channel.findall("item"))


def _atom_entries(root: ElementTree.Element) -> list[ElementTree.Element]:
    namespace = _namespace(root.tag)
    if namespace:
        return list(root.findall(f".//{{{namespace}}}entry"))
    return list(root.findall(".//entry"))


def _entry_title(item: ElementTree.Element) -> str:
    return (_find_text(item, "title") or "").strip()


def _entry_url(item: ElementTree.Element) -> str:
    link = _find_text(item, "link")
    if link:
        return link.strip()

    for child in item:
        if _local_name(child.tag) == "link":
            href = child.attrib.get("href")
            if href:
                return href.strip()
    return ""


def _entry_time(item: ElementTree.Element) -> str | None:
    raw = (
        _find_text(item, "pubDate")
        or _find_text(item, "updated")
        or _find_text(item, "published")
        or _find_text(item, "date")
    )
    if not raw:
        return None

    parsed = _parse_datetime(raw.strip())
    return parsed.isoformat() if parsed is not None else raw.strip()


def _find_text(item: ElementTree.Element, name: str) -> str | None:
    for child in item:
        if _local_name(child.tag) == name and child.text:
            return child.text
    return None


def _parse_datetime(value: str) -> datetime | None:
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        parsed = None
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _namespace(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag[1 : tag.index("}")]
    return ""


def _local_name(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag[tag.index("}") + 1 :]
    return tag


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def get_v2ex_rss_client(request: Request) -> V2exRssClient:
    return request.app.state.v2ex_rss_client
