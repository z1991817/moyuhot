from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.models.calendar import CalendarInfo

CHINA_TIME_ZONE = ZoneInfo("Asia/Shanghai")

HOLIDAYS_2026: dict[str, str] = {
    "2026-01-01": "元旦",
    "2026-01-02": "元旦",
    "2026-01-03": "元旦",
    "2026-02-15": "春节",
    "2026-02-16": "春节",
    "2026-02-17": "春节",
    "2026-02-18": "春节",
    "2026-02-19": "春节",
    "2026-02-20": "春节",
    "2026-02-21": "春节",
    "2026-02-22": "春节",
    "2026-02-23": "春节",
    "2026-04-04": "清明节",
    "2026-04-05": "清明节",
    "2026-04-06": "清明节",
    "2026-05-01": "劳动节",
    "2026-05-02": "劳动节",
    "2026-05-03": "劳动节",
    "2026-05-04": "劳动节",
    "2026-05-05": "劳动节",
    "2026-06-19": "端午节",
    "2026-06-20": "端午节",
    "2026-06-21": "端午节",
    "2026-09-25": "中秋节",
    "2026-09-26": "中秋节",
    "2026-09-27": "中秋节",
    "2026-10-01": "国庆节",
    "2026-10-02": "国庆节",
    "2026-10-03": "国庆节",
    "2026-10-04": "国庆节",
    "2026-10-05": "国庆节",
    "2026-10-06": "国庆节",
    "2026-10-07": "国庆节",
}

ADJUSTED_WORKDAYS_2026 = {
    "2026-01-04",
    "2026-02-14",
    "2026-02-28",
    "2026-05-09",
    "2026-09-20",
    "2026-10-10",
}


def _china_date(moment: datetime | None = None) -> date:
    if moment is None:
        moment = datetime.now(UTC)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=CHINA_TIME_ZONE)
    return moment.astimezone(CHINA_TIME_ZONE).date()


def get_china_rest_day_info(moment: datetime | None = None) -> CalendarInfo:
    day = _china_date(moment)
    date_str = day.isoformat()
    holiday_name = HOLIDAYS_2026.get(date_str)

    if holiday_name is not None:
        return CalendarInfo(
            date=date_str,
            is_rest_day=True,
            kind="holiday",
            name=holiday_name,
        )

    if day.weekday() >= 5 and date_str not in ADJUSTED_WORKDAYS_2026:
        return CalendarInfo(
            date=date_str,
            is_rest_day=True,
            kind="weekend",
            name="周末",
        )

    return CalendarInfo(
        date=date_str,
        is_rest_day=False,
        kind="workday",
    )
