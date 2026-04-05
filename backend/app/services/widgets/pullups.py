from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.timezone import UTC_TIMEZONE, local_day_bounds_utc, local_today
from app.models.exercise import Exercise
from app.models.exercise_log import ExerciseLog
from app.schemas.widget import PullupsWidgetDayItem, PullupsWidgetResponse
from app.services.shared.progress import (
    goal_intensity_level,
    grouped_day_expression,
    parse_grouped_day,
    relative_intensity_level,
)


def _daily_reps_map_for_exercise(
    db: Session,
    exercise_id: int,
    start: datetime,
    end: datetime,
    timezone: ZoneInfo,
) -> dict[date, int]:
    grouped_day = grouped_day_expression(db, timezone, ExerciseLog.logged_at)
    rows = db.execute(
        select(
            grouped_day.label("local_day"),
            func.coalesce(func.sum(ExerciseLog.reps), 0),
        )
        .where(
            and_(
                ExerciseLog.exercise_id == exercise_id,
                ExerciseLog.logged_at >= start,
                ExerciseLog.logged_at < end,
            )
        )
        .group_by(grouped_day)
        .order_by(grouped_day)
    ).all()

    return {parse_grouped_day(row[0]): int(row[1] or 0) for row in rows}


def get_pullups_widget(db: Session, timezone: ZoneInfo = UTC_TIMEZONE) -> PullupsWidgetResponse:
    pullups = db.scalar(select(Exercise).where(and_(Exercise.slug == "pullups", Exercise.deleted_at.is_(None))))
    if not pullups:
        raise HTTPException(status_code=404, detail="exercise not found")

    today = local_today(timezone)
    start_day = today - timedelta(days=29)
    year_start_day = date(today.year, 1, 1)

    start_30_days_utc, _ = local_day_bounds_utc(start_day, timezone)
    year_start_utc, _ = local_day_bounds_utc(year_start_day, timezone)
    _, tomorrow_start_utc = local_day_bounds_utc(today, timezone)

    year_total = db.scalar(
        select(func.coalesce(func.sum(ExerciseLog.reps), 0)).where(
            and_(
                ExerciseLog.exercise_id == pullups.id,
                ExerciseLog.logged_at >= year_start_utc,
                ExerciseLog.logged_at < tomorrow_start_utc,
            )
        )
    )
    daily_counts = _daily_reps_map_for_exercise(db, pullups.id, start_30_days_utc, tomorrow_start_utc, timezone)

    day_values: list[tuple[date, int]] = []
    for i in range(30):
        day = start_day + timedelta(days=i)
        day_values.append((day, daily_counts.get(day, 0)))

    daily_goal = pullups.goal_reps if pullups.goal_reps is not None and pullups.goal_reps > 0 else None
    peak_count = max((count for _, count in day_values), default=0)

    last_30_days = [
        PullupsWidgetDayItem(
            date=day,
            count=count,
            heat_level=(
                goal_intensity_level(count, daily_goal)
                if daily_goal is not None
                else relative_intensity_level(count, peak_count)
            ),
        )
        for day, count in day_values
    ]

    return PullupsWidgetResponse(
        year_total=int(year_total or 0),
        daily_goal=daily_goal,
        last_30_days=last_30_days,
    )
