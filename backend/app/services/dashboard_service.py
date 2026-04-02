from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.exercise import Exercise, MetricType
from app.models.exercise_log import ExerciseLog
from app.schemas.common import Totals
from app.schemas.dashboard import (
    BestDay,
    DailyTotalItem,
    DashboardSummaryResponse,
    ExerciseHistoryResponse,
    ExerciseMeta,
    ExerciseTotalsItem,
)
from app.schemas.log import RecentLogItem
from app.services.totals import totals_for_exercise


def _day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime(day.year, day.month, day.day, tzinfo=UTC)
    return start, start + timedelta(days=1)


def _metric_value(metric_type: MetricType, totals: Totals) -> int:
    if metric_type == MetricType.DURATION_SECONDS:
        return int(totals.duration_seconds or 0)
    return int(totals.reps or 0)


def _count_logs_in_window(db: Session, start: datetime, end: datetime) -> int:
    total = db.scalar(
        select(func.count(ExerciseLog.id)).where(
            and_(ExerciseLog.logged_at >= start, ExerciseLog.logged_at < end)
        )
    )
    return int(total or 0)


def _aggregate_by_exercise(db: Session, start: datetime, end: datetime) -> list[ExerciseTotalsItem]:
    window_totals = (
        select(
            ExerciseLog.exercise_id.label("exercise_id"),
            func.coalesce(func.sum(ExerciseLog.reps), 0).label("reps_total"),
            func.coalesce(func.sum(ExerciseLog.duration_seconds), 0).label("duration_total"),
        )
        .where(and_(ExerciseLog.logged_at >= start, ExerciseLog.logged_at < end))
        .group_by(ExerciseLog.exercise_id)
        .subquery()
    )

    rows = db.execute(
        select(
            Exercise.id,
            Exercise.slug,
            Exercise.name,
            Exercise.metric_type,
            func.coalesce(window_totals.c.reps_total, 0),
            func.coalesce(window_totals.c.duration_total, 0),
        )
        .select_from(Exercise)
        .join(window_totals, window_totals.c.exercise_id == Exercise.id, isouter=True)
        .order_by(Exercise.sort_order, Exercise.name)
    ).all()

    return [
        ExerciseTotalsItem(
            exercise_id=row[0],
            exercise_slug=row[1],
            exercise_name=row[2],
            metric_type=row[3],
            totals=Totals(reps=int(row[4]), duration_seconds=int(row[5])),
        )
        for row in rows
    ]


def get_summary(db: Session) -> DashboardSummaryResponse:
    now = datetime.now(UTC)
    today_start, end = _day_bounds(now.date())
    week_start = today_start - timedelta(days=now.weekday())

    today = _aggregate_by_exercise(db, today_start, end)
    current_week = _aggregate_by_exercise(db, week_start, end)
    last_30_days = _aggregate_by_exercise(db, today_start - timedelta(days=29), end)

    total_logs_today = _count_logs_in_window(db, today_start, end)
    total_logs_this_week = _count_logs_in_window(db, week_start, end)

    return DashboardSummaryResponse(
        today=today,
        current_week=current_week,
        last_30_days=last_30_days,
        total_logs_today=total_logs_today,
        total_logs_this_week=total_logs_this_week,
    )


def _streak(days: list[DailyTotalItem], metric_type: MetricType) -> int:
    streak = 0
    for item in reversed(days):
        if _metric_value(metric_type, item.totals) > 0:
            streak += 1
        else:
            break
    return streak


def _daily_totals_map(
    db: Session,
    exercise_id: int,
    start: datetime,
    end: datetime,
) -> dict[date, Totals]:
    rows = db.execute(
        select(
            func.date(ExerciseLog.logged_at),
            func.coalesce(func.sum(ExerciseLog.reps), 0),
            func.coalesce(func.sum(ExerciseLog.duration_seconds), 0),
        )
        .where(
            and_(
                ExerciseLog.exercise_id == exercise_id,
                ExerciseLog.logged_at >= start,
                ExerciseLog.logged_at < end,
            )
        )
        .group_by(func.date(ExerciseLog.logged_at))
        .order_by(func.date(ExerciseLog.logged_at))
    ).all()

    mapped: dict[date, Totals] = {}
    for row in rows:
        raw_day = row[0]
        parsed_day = raw_day if isinstance(raw_day, date) else date.fromisoformat(str(raw_day))
        mapped[parsed_day] = Totals(reps=int(row[1]), duration_seconds=int(row[2]))

    return mapped


def _build_days_and_best(
    start_day: date,
    day_count: int,
    metric_type: MetricType,
    totals_by_day: dict[date, Totals],
) -> tuple[list[DailyTotalItem], BestDay | None]:
    items: list[DailyTotalItem] = []
    best: BestDay | None = None

    for i in range(day_count):
        day = start_day + timedelta(days=i)
        totals = totals_by_day.get(day, Totals(reps=0, duration_seconds=0))
        items.append(DailyTotalItem(day=day, totals=totals))

        current_value = _metric_value(metric_type, totals)
        if current_value <= 0:
            continue

        if best is None:
            best = BestDay(day=day, totals=totals)
            continue

        if current_value > _metric_value(metric_type, best.totals):
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


def get_exercise_history(db: Session, slug: str, days: int) -> ExerciseHistoryResponse:
    exercise = db.scalar(select(Exercise).where(Exercise.slug == slug))
    if not exercise:
        raise HTTPException(status_code=404, detail="exercise not found")

    days = max(1, min(days, 365))
    today = datetime.now(UTC).date()
    start_day = today - timedelta(days=days - 1)
    start_today, end_today = _day_bounds(today)
    start_window, _ = _day_bounds(start_day)

    mapped = _daily_totals_map(db, exercise.id, start_window, end_today)
    items, best = _build_days_and_best(start_day, days, exercise.metric_type, mapped)

    all_time = totals_for_exercise(db, exercise.id)
    today_total = totals_for_exercise(db, exercise.id, start_today, end_today)
    last_7 = totals_for_exercise(db, exercise.id, end_today - timedelta(days=7), end_today)
    last_30 = totals_for_exercise(db, exercise.id, end_today - timedelta(days=30), end_today)
    recent_logs = _recent_logs_for_exercise(db, exercise)

    return ExerciseHistoryResponse(
        exercise=ExerciseMeta(
            id=exercise.id,
            slug=exercise.slug,
            name=exercise.name,
            metric_type=exercise.metric_type,
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
