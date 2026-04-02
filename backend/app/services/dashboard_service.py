from datetime import UTC, date, datetime, time, timedelta

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
    today_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
    week_start = today_start - timedelta(days=now.weekday())
    end = today_start + timedelta(days=1)

    today = _aggregate_by_exercise(db, today_start, end)
    current_week = _aggregate_by_exercise(db, week_start, end)
    last_30_days = _aggregate_by_exercise(db, today_start - timedelta(days=29), end)

    total_logs_today = db.scalar(
        select(func.count(ExerciseLog.id)).where(
            and_(ExerciseLog.logged_at >= today_start, ExerciseLog.logged_at < end)
        )
    )
    total_logs_this_week = db.scalar(
        select(func.count(ExerciseLog.id)).where(
            and_(ExerciseLog.logged_at >= week_start, ExerciseLog.logged_at < end)
        )
    )

    return DashboardSummaryResponse(
        today=today,
        current_week=current_week,
        last_30_days=last_30_days,
        total_logs_today=int(total_logs_today or 0),
        total_logs_this_week=int(total_logs_this_week or 0),
    )


def _streak(days: list[DailyTotalItem], metric_type: MetricType) -> int:
    streak = 0
    for item in reversed(days):
        value = item.totals.duration_seconds if metric_type == MetricType.DURATION_SECONDS else item.totals.reps
        if value and value > 0:
            streak += 1
        else:
            break
    return streak


def get_exercise_history(db: Session, slug: str, days: int) -> ExerciseHistoryResponse:
    exercise = db.scalar(select(Exercise).where(Exercise.slug == slug))
    if not exercise:
        raise HTTPException(status_code=404, detail="exercise not found")

    days = max(1, min(days, 365))
    today = datetime.now(UTC).date()
    start_day = today - timedelta(days=days - 1)
    start_dt = datetime.combine(start_day, time.min, tzinfo=UTC)
    end_dt = datetime.combine(today + timedelta(days=1), time.min, tzinfo=UTC)

    raw = db.execute(
        select(
            func.date(ExerciseLog.logged_at),
            func.coalesce(func.sum(ExerciseLog.reps), 0),
            func.coalesce(func.sum(ExerciseLog.duration_seconds), 0),
        )
        .where(
            and_(
                ExerciseLog.exercise_id == exercise.id,
                ExerciseLog.logged_at >= start_dt,
                ExerciseLog.logged_at < end_dt,
            )
        )
        .group_by(func.date(ExerciseLog.logged_at))
        .order_by(func.date(ExerciseLog.logged_at))
    ).all()
    mapped: dict[date, Totals] = {}
    for row in raw:
        raw_day = row[0]
        parsed_day = raw_day if isinstance(raw_day, date) else date.fromisoformat(str(raw_day))
        mapped[parsed_day] = Totals(reps=int(row[1]), duration_seconds=int(row[2]))

    items: list[DailyTotalItem] = []
    best: BestDay | None = None
    for i in range(days):
        d = start_day + timedelta(days=i)
        totals = mapped.get(d, Totals(reps=0, duration_seconds=0))
        items.append(DailyTotalItem(day=d, totals=totals))
        metric_value = totals.duration_seconds if exercise.metric_type == MetricType.DURATION_SECONDS else totals.reps
        if metric_value and metric_value > 0:
            if not best:
                best = BestDay(day=d, totals=totals)
            else:
                best_metric = (
                    best.totals.duration_seconds
                    if exercise.metric_type == MetricType.DURATION_SECONDS
                    else best.totals.reps
                )
                if metric_value > (best_metric or 0):
                    best = BestDay(day=d, totals=totals)

    start_today = datetime.combine(today, time.min, tzinfo=UTC)
    end_today = start_today + timedelta(days=1)
    all_time = totals_for_exercise(db, exercise.id)
    today_total = totals_for_exercise(db, exercise.id, start_today, end_today)
    last_7 = totals_for_exercise(db, exercise.id, end_today - timedelta(days=7), end_today)
    last_30 = totals_for_exercise(db, exercise.id, end_today - timedelta(days=30), end_today)

    recent = db.execute(
        select(ExerciseLog)
        .where(ExerciseLog.exercise_id == exercise.id)
        .order_by(ExerciseLog.logged_at.desc())
        .limit(20)
    ).scalars().all()

    recent_logs = [
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
        for log in recent
    ]

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
