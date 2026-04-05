from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.timezone import UTC_TIMEZONE, local_day_bounds_utc, local_today
from app.models.exercise import Exercise, MetricType
from app.models.exercise_log import ExerciseLog
from app.schemas.common import Totals
from app.schemas.dashboard import (
    ConsistencyDayItem,
    DashboardSummaryResponse,
    ExerciseConsistencyItem,
    ExerciseTotalsItem,
)
from app.services.shared.progress import (
    goal_intensity_level,
    goal_target_value,
    grouped_day_expression,
    metric_value,
    parse_grouped_day,
    relative_intensity_level,
)


def _count_logs_in_window(db: Session, start: datetime, end: datetime) -> int:
    total = db.scalar(
        select(func.count(ExerciseLog.id))
        .select_from(ExerciseLog)
        .join(Exercise, Exercise.id == ExerciseLog.exercise_id)
        .where(
            and_(
                ExerciseLog.logged_at >= start,
                ExerciseLog.logged_at < end,
                Exercise.deleted_at.is_(None),
            )
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
        .where(Exercise.deleted_at.is_(None))
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


def _daily_totals_and_log_counts_by_exercise(
    db: Session,
    start: datetime,
    end: datetime,
    timezone: ZoneInfo,
) -> tuple[dict[int, dict[date, Totals]], dict[int, int]]:
    grouped_day = grouped_day_expression(db, timezone, ExerciseLog.logged_at)
    rows = db.execute(
        select(
            ExerciseLog.exercise_id,
            grouped_day.label("local_day"),
            func.coalesce(func.sum(ExerciseLog.reps), 0),
            func.coalesce(func.sum(ExerciseLog.duration_seconds), 0),
            func.count(ExerciseLog.id),
        )
        .select_from(ExerciseLog)
        .join(Exercise, Exercise.id == ExerciseLog.exercise_id)
        .where(
            and_(
                ExerciseLog.logged_at >= start,
                ExerciseLog.logged_at < end,
                Exercise.deleted_at.is_(None),
            )
        )
        .group_by(ExerciseLog.exercise_id, grouped_day)
        .order_by(ExerciseLog.exercise_id, grouped_day)
    ).all()

    totals_by_exercise: dict[int, dict[date, Totals]] = {}
    log_count_by_exercise: dict[int, int] = {}

    for row in rows:
        exercise_id = int(row[0])
        parsed_day = parse_grouped_day(row[1])
        totals_by_exercise.setdefault(exercise_id, {})[parsed_day] = Totals(
            reps=int(row[2] or 0),
            duration_seconds=int(row[3] or 0),
        )
        log_count_by_exercise[exercise_id] = log_count_by_exercise.get(exercise_id, 0) + int(row[4] or 0)

    return totals_by_exercise, log_count_by_exercise


def _daily_goal_weighted_reps_by_exercise(
    db: Session,
    start: datetime,
    end: datetime,
    timezone: ZoneInfo,
) -> dict[int, dict[date, int]]:
    grouped_day = grouped_day_expression(db, timezone, ExerciseLog.logged_at)
    rows = db.execute(
        select(
            ExerciseLog.exercise_id,
            grouped_day.label("local_day"),
            func.coalesce(func.sum(ExerciseLog.reps), 0),
        )
        .select_from(ExerciseLog)
        .join(Exercise, Exercise.id == ExerciseLog.exercise_id)
        .where(
            and_(
                ExerciseLog.logged_at >= start,
                ExerciseLog.logged_at < end,
                Exercise.deleted_at.is_(None),
                Exercise.metric_type == MetricType.REPS_PLUS_WEIGHT_LBS,
                Exercise.goal_weight_lbs.is_not(None),
                ExerciseLog.weight_lbs >= Exercise.goal_weight_lbs,
            )
        )
        .group_by(ExerciseLog.exercise_id, grouped_day)
        .order_by(ExerciseLog.exercise_id, grouped_day)
    ).all()

    weighted_reps_by_exercise: dict[int, dict[date, int]] = {}
    for row in rows:
        exercise_id = int(row[0])
        parsed_day = parse_grouped_day(row[1])
        weighted_reps_by_exercise.setdefault(exercise_id, {})[parsed_day] = int(row[2] or 0)

    return weighted_reps_by_exercise


def _goals_by_exercise(
    db: Session,
    exercise_ids: list[int],
) -> dict[int, tuple[int | None, int | None, float | None]]:
    if not exercise_ids:
        return {}

    rows = db.execute(
        select(Exercise.id, Exercise.goal_reps, Exercise.goal_duration_seconds, Exercise.goal_weight_lbs)
        .where(and_(Exercise.id.in_(exercise_ids), Exercise.deleted_at.is_(None)))
    ).all()

    return {
        int(row[0]): (
            int(row[1]) if row[1] is not None else None,
            int(row[2]) if row[2] is not None else None,
            float(row[3]) if row[3] is not None else None,
        )
        for row in rows
    }


def _build_last_30_days_consistency(
    db: Session,
    items: list[ExerciseTotalsItem],
    start_day: date,
    end: datetime,
    timezone: ZoneInfo,
) -> list[ExerciseConsistencyItem]:
    start, _ = local_day_bounds_utc(start_day, timezone)
    totals_map, log_count_map = _daily_totals_and_log_counts_by_exercise(db, start, end, timezone)
    weighted_map = _daily_goal_weighted_reps_by_exercise(db, start, end, timezone)
    goals_map = _goals_by_exercise(db, [item.exercise_id for item in items])

    consistency: list[ExerciseConsistencyItem] = []
    for item in items:
        per_day = totals_map.get(item.exercise_id, {})
        weighted_per_day = weighted_map.get(item.exercise_id, {})
        day_items_seed: list[tuple[date, Totals, int]] = []
        active_days = 0
        goal_reps, goal_duration_seconds, goal_weight_lbs = goals_map.get(item.exercise_id, (None, None, None))
        current_goal_target = goal_target_value(
            item.metric_type,
            goal_reps,
            goal_duration_seconds,
            goal_weight_lbs,
        )
        scaling_mode = "goal" if current_goal_target is not None else "relative"

        for i in range(30):
            day = start_day + timedelta(days=i)
            totals = per_day.get(day, Totals(reps=0, duration_seconds=0))
            if metric_value(item.metric_type, totals) > 0:
                active_days += 1

            progress_value = metric_value(item.metric_type, totals)
            if item.metric_type == MetricType.REPS_PLUS_WEIGHT_LBS and current_goal_target is not None:
                progress_value = weighted_per_day.get(day, 0)

            day_items_seed.append((day, totals, progress_value))

        peak_progress = max((seed[2] for seed in day_items_seed), default=0)
        day_items: list[ConsistencyDayItem] = []
        for day, totals, progress_value in day_items_seed:
            if current_goal_target is not None:
                intensity_level = goal_intensity_level(progress_value, current_goal_target)
            else:
                intensity_level = relative_intensity_level(progress_value, peak_progress)
            day_items.append(
                ConsistencyDayItem(
                    day=day,
                    totals=totals,
                    progress_value=progress_value,
                    intensity_level=intensity_level,
                )
            )

        consistency.append(
            ExerciseConsistencyItem(
                exercise_id=item.exercise_id,
                exercise_slug=item.exercise_slug,
                exercise_name=item.exercise_name,
                metric_type=item.metric_type,
                window_totals=item.totals,
                active_days=active_days,
                total_logs=log_count_map.get(item.exercise_id, 0),
                scaling_mode=scaling_mode,
                goal_target_value=current_goal_target,
                goal_weight_lbs=goal_weight_lbs,
                days=day_items,
            )
        )

    return consistency


def get_summary(db: Session, timezone: ZoneInfo = UTC_TIMEZONE) -> DashboardSummaryResponse:
    today_local = local_today(timezone)
    today_start, end = local_day_bounds_utc(today_local, timezone)
    week_start = today_start - timedelta(days=today_local.weekday())
    last_30_start = today_start - timedelta(days=29)

    today = _aggregate_by_exercise(db, today_start, end)
    current_week = _aggregate_by_exercise(db, week_start, end)
    last_30_days = _aggregate_by_exercise(db, last_30_start, end)
    last_30_days_consistency = _build_last_30_days_consistency(
        db,
        last_30_days,
        (today_local - timedelta(days=29)),
        end,
        timezone,
    )

    total_logs_today = _count_logs_in_window(db, today_start, end)
    total_logs_this_week = _count_logs_in_window(db, week_start, end)

    return DashboardSummaryResponse(
        today=today,
        current_week=current_week,
        last_30_days=last_30_days,
        last_30_days_consistency=last_30_days_consistency,
        total_logs_today=total_logs_today,
        total_logs_this_week=total_logs_this_week,
    )
