from __future__ import annotations

from datetime import UTC, datetime

import httpx
from fastapi import Request
from pydantic import ValidationError

from app.config import settings
from app.models.source import Source
from app.models.trend import Trend
from app.platforms import get_platform_name


class SeeSeaError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class SeeSeaClient:
    def __init__(
        self,
        base_url: str | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=(base_url or settings.seesea_base_url).rstrip("/"),
            timeout=httpx.Timeout(8.0, connect=3.0),
            headers={"User-Agent": "moyu-aggregator/0.1"},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def fetch_multiple(self, platforms: list[str]) -> list[Trend]:
        payload = await self._get_json(
            "/api/hot/multiple", {"platforms": ",".join(platforms), "latest": "true"}
        )
        return self._parse_multi_payload(payload)

    async def fetch_single(self, platform: str) -> list[Trend]:
        payload = await self._get_json(f"/api/hot/{platform}", {"latest": "true"})
        return self._parse_single_payload(payload, platform)

    async def fetch_platforms(self) -> list[Source]:
        payload = await self._get_json("/api/hot/platforms", None)
        now = _now_iso()
        if isinstance(payload, list):
            return [
                Source(
                    platform=str(item.get("id") or item.get("platform_id") or ""),
                    platform_name=str(item.get("name") or item.get("platform_name") or ""),
                    status="ok",
                    updated_at=now,
                )
                for item in payload
                if isinstance(item, dict)
            ]
        if isinstance(payload, dict):
            return [
                Source(
                    platform=str(platform),
                    platform_name=str(platform_name),
                    status="ok",
                    updated_at=now,
                )
                for platform, platform_name in payload.items()
            ]
        return []

    async def _get_json(self, path: str, params: dict[str, str] | None) -> object:
        try:
            response = await self._client.get(path, params=params)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise SeeSeaError("SEESEA_UPSTREAM", "上游数据源暂不可用") from exc

    def _parse_multi_payload(self, payload: object) -> list[Trend]:
        groups = []
        if isinstance(payload, list):
            groups = payload
        elif isinstance(payload, dict):
            results = payload.get("results")
            if isinstance(results, list):
                groups = results
            elif all(isinstance(v, dict) for v in payload.values()):
                groups = list(payload.values())

        trends: list[Trend] = []
        now = _now_iso()
        for group in groups:
            if not isinstance(group, dict):
                continue
            platform = str(group.get("platform_id") or group.get("platform") or "")
            platform_name = str(group.get("platform_name") or get_platform_name(platform))
            items = group.get("items")
            if not isinstance(items, list):
                continue
            for idx, item in enumerate(items, start=1):
                if not isinstance(item, dict):
                    continue
                trend = _map_item(item, platform, platform_name, idx, now)
                if trend is not None:
                    trends.append(trend)
        return trends

    def _parse_single_payload(self, payload: object, platform: str) -> list[Trend]:
        if not isinstance(payload, dict):
            return []
        platform_name = str(payload.get("platform_name") or get_platform_name(platform))
        items = payload.get("items")
        if not isinstance(items, list):
            return []
        now = _now_iso()
        trends: list[Trend] = []
        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue
            trend = _map_item(item, platform, platform_name, idx, now)
            if trend is not None:
                trends.append(trend)
        return trends


def _map_item(
    item: dict[str, object], platform: str, platform_name: str, rank: int, fallback_time: str
) -> Trend | None:
    title = str(item.get("title") or "").strip()
    url = str(item.get("url") or item.get("mobileUrl") or item.get("mobile_url") or "").strip()
    if not title or not url:
        return None

    raw_rank = item.get("rank")
    if isinstance(raw_rank, int):
        rank = raw_rank

    heat_value = item.get("hotValue") or item.get("hot_value")
    heat = str(heat_value) if heat_value is not None else str(item.get("hotIndex") or "")
    updated_at = str(item.get("publishTime") or fallback_time)

    try:
        return Trend(
            platform=platform,
            platform_name=platform_name,
            title=title,
            url=url,
            rank=rank,
            heat=heat,
            source=str(item.get("source") or platform),
            updated_at=updated_at,
        )
    except ValidationError:
        return None


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def get_seesea_client(request: Request) -> SeeSeaClient:
    return request.app.state.seesea_client
