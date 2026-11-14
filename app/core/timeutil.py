from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

TAIPEI = ZoneInfo("Asia/Taipei")


def taipei_now() -> datetime:
    return datetime.now(TAIPEI)


def taipei_today() -> date:
    return taipei_now().date()


def as_taipei(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=TAIPEI)
    return value.astimezone(TAIPEI)


def day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=TAIPEI)
    return start, start + timedelta(days=1)


def month_bounds(day: date) -> tuple[datetime, datetime, date, date]:
    period_start = day.replace(day=1)
    if day.month == 12:
        next_month = date(day.year + 1, 1, 1)
    else:
        next_month = date(day.year, day.month + 1, 1)
    period_end = next_month - timedelta(days=1)
    start = datetime.combine(period_start, time.min, tzinfo=TAIPEI)
    end = datetime.combine(next_month, time.min, tzinfo=TAIPEI)
    return start, end, period_start, period_end
