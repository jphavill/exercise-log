from datetime import date, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.timezone import UTC_TIMEZONE, training_today
from app.models.exercise import Exercise, MetricType
from app.models.exercise_log import ExerciseLog
from app.schemas.common import Totals
from app.schemas.dashboard import BestDay, DailyTotalItem, ExerciseHistoryResponse, ExerciseMeta
from app.schemas.log import RecentLogItem
from app.services.shared.progress import grouped_day_expression, metric_value, parse_grouped_day
from app.services.totals import totals_for_exercise, totals_for_exercise_training_days


def _streak(days: list[DailyTotalItem], metric_type: MetricType) -> int:
    streak = 0
    for item in reversed(days):
        if metric_value(metric_type, item.totals) > 0:
            streak += 1
        else:
            break
    return streak


def _daily_totals_map(
    db: Session,
    exercise_id: int,
    start_day: date,
    end_day_exclusive: date,
    timezone: ZoneInfo,
) -> dict[date, Totals]:
    grouped_day = grouped_day_expression(db, timezone, ExerciseLog.logged_at)
    rows = db.execute(
        select(
            grouped_day.label("local_day"),
            func.coalesce(func.sum(ExerciseLog.reps), 0),
            func.coalesce(func.sum(ExerciseLog.duration_seconds), 0),
        )
        .where(
            and_(
                ExerciseLog.exercise_id == exercise_id,
                grouped_day >= start_day,
                grouped_day < end_day_exclusive,
            )
        )
        .group_by(grouped_day)
        .order_by(grouped_day)
    ).all()

    return {
        parse_grouped_day(row[0]): Totals(reps=int(row[1] or 0), duration_seconds=int(row[2] or 0))
        for row in rows
    }


def _daily_weighted_goal_reps_map(
    db: Session,
    exercise_id: int,
    start_day: date,
    end_day_exclusive: date,
    goal_weight_lbs: float,
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
                grouped_day >= start_day,
                grouped_day < end_day_exclusive,
                ExerciseLog.weight_lbs >= goal_weight_lbs,
            )
        )
        .group_by(grouped_day)
        .order_by(grouped_day)
    ).all()

    return {parse_grouped_day(row[0]): int(row[1] or 0) for row in rows}


def _build_days_and_best(
    start_day: date,
    day_count: int,
    metric_type: MetricType,
    totals_by_day: dict[date, Totals],
    weighted_goal_reps_by_day: dict[date, int] | None = None,
) -> tuple[list[DailyTotalItem], BestDay | None]:
    items: list[DailyTotalItem] = []
    best: BestDay | None = None

    for i in range(day_count):
        day = start_day + timedelta(days=i)
        totals = totals_by_day.get(day, Totals(reps=0, duration_seconds=0))
        goal_progress_value = metric_value(metric_type, totals)
        if metric_type == MetricType.REPS_PLUS_WEIGHT_LBS and weighted_goal_reps_by_day is not None:
            goal_progress_value = weighted_goal_reps_by_day.get(day, 0)
        items.append(DailyTotalItem(day=day, totals=totals, goal_progress_value=goal_progress_value))

        current_value = metric_value(metric_type, totals)
        if current_value <= 0:
            continue

        if best is None:
            best = BestDay(day=day, totals=totals)
            continue

        if current_value > metric_value(metric_type, best.totals):
            best = BestDay(day=day, totals=totals)

    return items, best


def _recent_logs_for_exercise(db: Session, exercise: Exercise, limit: int = 20) -> list[RecentLogItem]:
    logs = db.execute(
        select(ExerciseLog)
        .where(ExerciseLog.exercise_id == exercise.id)
        .order_by(ExerciseLog.logged_at.desc())
        .limit(limit)
    ).scalars().all()

    return [
        RecentLogItem(
            id=log.id,
            exercise_slug=exercise.slug,
            exercise_name=exercise.name,
            metric_type=exercise.metric_type,
            reps=log.reps,
            duration_seconds=log.duration_seconds,
            weight_lbs=float(log.weight_lbs) if log.weight_lbs is not None else None,
            notes=log.notes,
            logged_at=log.logged_at,
        )
        for log in logs
    ]


def get_exercise_history(
    db: Session,
    slug: str,
    days: int,
    timezone: ZoneInfo = UTC_TIMEZONE,
) -> ExerciseHistoryResponse:
    exercise = db.scalar(select(Exercise).where(and_(Exercise.slug == slug, Exercise.deleted_at.is_(None))))
    if not exercise:
        raise HTTPException(status_code=404, detail="exercise not found")

    days = max(1, min(days, 365))
    today = training_today(timezone)
    start_day = today - timedelta(days=days - 1)
    end_day_exclusive = today + timedelta(days=1)

    mapped = _daily_totals_map(db, exercise.id, start_day, end_day_exclusive, timezone)
    weighted_goal_reps_by_day: dict[date, int] | None = None
    if exercise.metric_type == MetricType.REPS_PLUS_WEIGHT_LBS and exercise.goal_weight_lbs is not None:
        weighted_goal_reps_by_day = _daily_weighted_goal_reps_map(
            db,
            exercise.id,
            start_day,
            end_day_exclusive,
            float(exercise.goal_weight_lbs),
            timezone,
        )

    items, best = _build_days_and_best(
        start_day,
        days,
        exercise.metric_type,
        mapped,
        weighted_goal_reps_by_day=weighted_goal_reps_by_day,
    )

    all_time = totals_for_exercise(db, exercise.id)
    today_total = totals_for_exercise_training_days(
        db,
        exercise.id,
        timezone,
        start_day=today,
        end_day_exclusive=end_day_exclusive,
    )
    last_7 = totals_for_exercise_training_days(
        db,
        exercise.id,
        timezone,
        start_day=today - timedelta(days=6),
        end_day_exclusive=end_day_exclusive,
    )
    last_30 = totals_for_exercise_training_days(
        db,
        exercise.id,
        timezone,
        start_day=today - timedelta(days=29),
        end_day_exclusive=end_day_exclusive,
    )
    recent_logs = _recent_logs_for_exercise(db, exercise)

    return ExerciseHistoryResponse(
        exercise=ExerciseMeta(
            id=exercise.id,
            slug=exercise.slug,
            name=exercise.name,
            metric_type=exercise.metric_type,
            sort_order=exercise.sort_order,
            goal_reps=exercise.goal_reps,
            goal_duration_seconds=exercise.goal_duration_seconds,
            goal_weight_lbs=float(exercise.goal_weight_lbs) if exercise.goal_weight_lbs is not None else None,
        ),
        days=items,
        current_streak=_streak(items, exercise.metric_type),
        best_day=best,
        all_time_total=all_time,
        today_total=today_total,
        last_7_days_total=last_7,
        last_30_days_total=last_30,
        recent_logs=recent_logs,
    )
