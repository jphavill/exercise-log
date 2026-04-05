from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.core.timezone import local_day_sql
from app.models.exercise import MetricType
from app.schemas.common import Totals


def parse_grouped_day(value: date | str | datetime) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value))


def grouped_day_expression(
    db: Session,
    timezone: ZoneInfo,
    timestamp_column: ColumnElement[datetime],
) -> ColumnElement[date]:
    bind = db.get_bind()
    dialect_name = bind.dialect.name if bind is not None else ""
    return local_day_sql(timestamp_column, timezone, dialect_name)


def metric_value(metric_type: MetricType, totals: Totals) -> int:
    if metric_type == MetricType.DURATION_SECONDS:
        return int(totals.duration_seconds or 0)
    return int(totals.reps or 0)


def goal_target_value(
    metric_type: MetricType,
    goal_reps: int | None,
    goal_duration_seconds: int | None,
    goal_weight_lbs: float | None,
) -> int | None:
    if metric_type == MetricType.REPS:
        return goal_reps if goal_reps and goal_reps > 0 else None
    if metric_type == MetricType.DURATION_SECONDS:
        return goal_duration_seconds if goal_duration_seconds and goal_duration_seconds > 0 else None
    if goal_reps and goal_reps > 0 and goal_weight_lbs and goal_weight_lbs > 0:
        return goal_reps
    return None


def goal_intensity_level(progress_value: int, goal_target_value: int) -> int:
    if progress_value <= 0:
        return 0

    ratio = progress_value / goal_target_value
    if ratio < 0.9:
        return 1
    if ratio <= 1.1:
        return 2
    if ratio < 2:
        return 3
    return 4


def relative_intensity_level(progress_value: int, peak_value: int) -> int:
    if progress_value <= 0 or peak_value <= 0:
        return 0

    ratio = progress_value / peak_value
    if ratio >= 0.75:
        return 4
    if ratio >= 0.5:
        return 3
    if ratio >= 0.25:
        return 2
    return 1
