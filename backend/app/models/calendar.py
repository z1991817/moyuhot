from __future__ import annotations

from typing import Literal

from app.models.common import APIModel

RestDayKind = Literal["holiday", "weekend", "workday"]


class CalendarInfo(APIModel):
    date: str
    is_rest_day: bool
    kind: RestDayKind
    name: str | None = None
