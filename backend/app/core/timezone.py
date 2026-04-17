from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import Date, func
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.functions import Function

UTC_TIMEZONE = ZoneInfo("UTC")
TRAINING_DAY_CUTOFF_HOURS = 3


def resolve_timezone(timezone_name: str | None) -> ZoneInfo:
    candidate = (timezone_name or "").strip()
    if candidate:
        try:
            return ZoneInfo(candidate)
        except ZoneInfoNotFoundError:
            return UTC_TIMEZONE
    return UTC_TIMEZONE


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def local_day_bounds_utc(day: date, timezone: ZoneInfo) -> tuple[datetime, datetime]:
    start_local = datetime(day.year, day.month, day.day, tzinfo=timezone)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def local_today(timezone: ZoneInfo) -> date:
    return datetime.now(UTC).astimezone(timezone).date()


def local_date_for_timestamp(value: datetime, timezone: ZoneInfo) -> date:
    return ensure_utc(value).astimezone(timezone).date()


def training_day_for_timestamp(value: datetime, timezone: ZoneInfo) -> date:
    local_value = ensure_utc(value).astimezone(timezone)
    return (local_value - timedelta(hours=TRAINING_DAY_CUTOFF_HOURS)).date()


def training_today(timezone: ZoneInfo) -> date:
    return training_day_for_timestamp(datetime.now(UTC), timezone)


def training_day_bounds_utc(day: date, timezone: ZoneInfo) -> tuple[datetime, datetime]:
    start_local = datetime(day.year, day.month, day.day, TRAINING_DAY_CUTOFF_HOURS, tzinfo=timezone)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def training_day_sql(
    timestamp_column: ColumnElement[datetime],
    timezone: ZoneInfo,
    dialect_name: str,
) -> ColumnElement[date] | Function[date]:
    if dialect_name == "postgresql":
        return func.date(
            func.timezone(timezone.key, timestamp_column) - timedelta(hours=TRAINING_DAY_CUTOFF_HOURS)
        )

    if dialect_name == "sqlite":
        return func.training_day_utc_iso(
            timestamp_column,
            timezone.key,
            TRAINING_DAY_CUTOFF_HOURS,
            type_=Date,
        )

    raise NotImplementedError(f"Unsupported SQL dialect for training-day grouping: {dialect_name}")
