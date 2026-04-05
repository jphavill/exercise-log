from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.orm import Session

from app.core.timezone import (
    UTC_TIMEZONE,
    local_day_bounds_utc,
    local_day_sql,
    local_today,
)
from app.models.exercise import Exercise, MetricType
from app.models.exercise_log import ExerciseLog
from app.schemas.common import Totals
from app.schemas.dashboard import (
    BestDay,
    ConsistencyDayItem,
    DailyTotalItem,
    DashboardSummaryResponse,
    ExerciseConsistencyItem,
    ExerciseHistoryResponse,
    ExerciseMeta,
    ExerciseTotalsItem,
)
from app.schemas.log import RecentLogItem
from app.schemas.widget import PullupsWidgetDayItem, PullupsWidgetResponse
from app.services.totals import totals_for_exercise


def _parse_grouped_day(value: date | str | datetime) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value))


def _grouped_day_expression(db: Session, timezone: ZoneInfo, timestamp_column: ColumnElement[datetime]) -> ColumnElement[date]:
    bind = db.get_bind()
    dialect_name = bind.dialect.name if bind is not None else ""
    return local_day_sql(timestamp_column, timezone, dialect_name)


def _metric_value(metric_type: MetricType, totals: Totals) -> int:
    if metric_type == MetricType.DURATION_SECONDS:
        return int(totals.duration_seconds or 0)
    return int(totals.reps or 0)


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
    grouped_day = _grouped_day_expression(db, timezone, ExerciseLog.logged_at)
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
        parsed_day = _parse_grouped_day(row[1])
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
    grouped_day = _grouped_day_expression(db, timezone, ExerciseLog.logged_at)
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
        parsed_day = _parse_grouped_day(row[1])
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


def _goal_target_value(
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


def _goal_intensity_level(progress_value: int, goal_target_value: int) -> int:
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


def _relative_intensity_level(progress_value: int, peak_value: int) -> int:
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


def _daily_reps_map_for_exercise(
    db: Session,
    exercise_id: int,
    start: datetime,
    end: datetime,
    timezone: ZoneInfo,
) -> dict[date, int]:
    grouped_day = _grouped_day_expression(db, timezone, ExerciseLog.logged_at)
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

    return {_parse_grouped_day(row[0]): int(row[1] or 0) for row in rows}


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
                _goal_intensity_level(count, daily_goal)
                if daily_goal is not None
                else _relative_intensity_level(count, peak_count)
            ),
        )
        for day, count in day_values
    ]

    return PullupsWidgetResponse(
        year_total=int(year_total or 0),
        daily_goal=daily_goal,
        last_30_days=last_30_days,
    )


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
        goal_target_value = _goal_target_value(item.metric_type, goal_reps, goal_duration_seconds, goal_weight_lbs)
        scaling_mode = "goal" if goal_target_value is not None else "relative"

        for i in range(30):
            day = start_day + timedelta(days=i)
            totals = per_day.get(day, Totals(reps=0, duration_seconds=0))
            if _metric_value(item.metric_type, totals) > 0:
                active_days += 1

            progress_value = _metric_value(item.metric_type, totals)
            if item.metric_type == MetricType.REPS_PLUS_WEIGHT_LBS and goal_target_value is not None:
                progress_value = weighted_per_day.get(day, 0)

            day_items_seed.append((day, totals, progress_value))

        peak_progress = max((seed[2] for seed in day_items_seed), default=0)
        day_items: list[ConsistencyDayItem] = []
        for day, totals, progress_value in day_items_seed:
            if goal_target_value is not None:
                intensity_level = _goal_intensity_level(progress_value, goal_target_value)
            else:
                intensity_level = _relative_intensity_level(progress_value, peak_progress)
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
                goal_target_value=goal_target_value,
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
    timezone: ZoneInfo,
) -> dict[date, Totals]:
    grouped_day = _grouped_day_expression(db, timezone, ExerciseLog.logged_at)
    rows = db.execute(
        select(
            grouped_day.label("local_day"),
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
        .group_by(grouped_day)
        .order_by(grouped_day)
    ).all()

    return {
        _parse_grouped_day(row[0]): Totals(reps=int(row[1] or 0), duration_seconds=int(row[2] or 0))
        for row in rows
    }


def _daily_weighted_goal_reps_map(
    db: Session,
    exercise_id: int,
    start: datetime,
    end: datetime,
    goal_weight_lbs: float,
    timezone: ZoneInfo,
) -> dict[date, int]:
    grouped_day = _grouped_day_expression(db, timezone, ExerciseLog.logged_at)
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
                ExerciseLog.weight_lbs >= goal_weight_lbs,
            )
        )
        .group_by(grouped_day)
        .order_by(grouped_day)
    ).all()

    return {_parse_grouped_day(row[0]): int(row[1] or 0) for row in rows}


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
        goal_progress_value = _metric_value(metric_type, totals)
        if metric_type == MetricType.REPS_PLUS_WEIGHT_LBS and weighted_goal_reps_by_day is not None:
            goal_progress_value = weighted_goal_reps_by_day.get(day, 0)
        items.append(DailyTotalItem(day=day, totals=totals, goal_progress_value=goal_progress_value))

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


def get_exercise_history(
    db: Session, slug: str, days: int, timezone: ZoneInfo = UTC_TIMEZONE
) -> ExerciseHistoryResponse:
    exercise = db.scalar(select(Exercise).where(and_(Exercise.slug == slug, Exercise.deleted_at.is_(None))))
    if not exercise:
        raise HTTPException(status_code=404, detail="exercise not found")

    days = max(1, min(days, 365))
    today = local_today(timezone)
    start_day = today - timedelta(days=days - 1)
    start_today, end_today = local_day_bounds_utc(today, timezone)
    start_window, _ = local_day_bounds_utc(start_day, timezone)

    mapped = _daily_totals_map(db, exercise.id, start_window, end_today, timezone)
    weighted_goal_reps_by_day: dict[date, int] | None = None
    if exercise.metric_type == MetricType.REPS_PLUS_WEIGHT_LBS and exercise.goal_weight_lbs is not None:
        weighted_goal_reps_by_day = _daily_weighted_goal_reps_map(
            db,
            exercise.id,
            start_window,
            end_today,
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
