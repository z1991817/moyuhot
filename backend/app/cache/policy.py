from __future__ import annotations

from typing import TypeVar

from pydantic import ValidationError

from app.cache.sqlite import SQLiteCache
from app.config import settings
from app.models.common import APIModel

ResponseT = TypeVar("ResponseT", bound=APIModel)


async def get_cached_response(
    cache: SQLiteCache, key: str, model: type[ResponseT]
) -> tuple[ResponseT, bool] | None:
    cached = await cache.get(key)
    if cached is None:
        return None

    payload, is_expired = cached
    try:
        return model.model_validate(payload), is_expired
    except ValidationError:
        return None


def as_fresh(response: ResponseT) -> ResponseT:
    return response.model_copy(update={"stale": False})


def as_stale(response: ResponseT) -> ResponseT:
    return response.model_copy(update={"stale": True})


def market_ttl_seconds(market_status: str) -> int:
    if market_status == "open":
        return settings.market_open_cache_ttl_seconds
    return settings.market_closed_cache_ttl_seconds
