from datetime import UTC, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.exercise import Exercise, MetricType
from app.models.exercise_log import ExerciseLog
from app.core.timezone import UTC_TIMEZONE, local_day_bounds_utc, local_today
from app.schemas.log import CreateLogRequest, LogResponse, RecentLogItem
from app.services.totals import totals_for_exercise


def _validate_payload(metric_type: MetricType, payload: CreateLogRequest) -> None:
    if metric_type == MetricType.DURATION_SECONDS:
        if payload.duration_seconds is None or payload.reps is not None or payload.weight_lbs is not None:
            raise HTTPException(status_code=422, detail="duration_seconds exercises require duration_seconds only")
    elif metric_type == MetricType.REPS:
        if payload.reps is None or payload.duration_seconds is not None or payload.weight_lbs is not None:
            raise HTTPException(status_code=422, detail="reps exercises require reps only")
    elif metric_type == MetricType.REPS_PLUS_WEIGHT_LBS:
        if payload.reps is None or payload.weight_lbs is None or payload.duration_seconds is not None:
            raise HTTPException(
                status_code=422,
                detail="reps_plus_weight_lbs exercises require reps and weight_lbs",
            )


def create_log(db: Session, payload: CreateLogRequest, timezone: ZoneInfo = UTC_TIMEZONE) -> LogResponse:
    exercise = db.scalar(
        select(Exercise).where(
            and_(Exercise.slug == payload.exercise_slug, Exercise.deleted_at.is_(None))
        )
    )
    if not exercise:
        raise HTTPException(status_code=404, detail="exercise_slug not found")

    _validate_payload(exercise.metric_type, payload)

    now = datetime.now(UTC)
    log = ExerciseLog(
        exercise_id=exercise.id,
        logged_at=now,
        reps=payload.reps,
        duration_seconds=payload.duration_seconds,
        weight_lbs=Decimal(str(payload.weight_lbs)) if payload.weight_lbs is not None else None,
        notes=payload.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    today = local_today(timezone)
    today_start, tomorrow_start = local_day_bounds_utc(today, timezone)
    week_start = today_start - timedelta(days=6)

    today_total = totals_for_exercise(db, exercise.id, today_start, tomorrow_start)
    last_7_days_total = totals_for_exercise(db, exercise.id, week_start, tomorrow_start)

    return LogResponse(
        id=log.id,
        exercise_slug=exercise.slug,
        reps=log.reps,
        duration_seconds=log.duration_seconds,
        weight_lbs=float(log.weight_lbs) if log.weight_lbs is not None else None,
        logged_at=log.logged_at,
        today_total=today_total,
        last_7_days_total=last_7_days_total,
    )


def get_recent_logs(db: Session, limit: int) -> list[RecentLogItem]:
    rows = db.execute(
        select(ExerciseLog, Exercise.slug, Exercise.name, Exercise.metric_type)
        .join(Exercise, Exercise.id == ExerciseLog.exercise_id)
        .where(Exercise.deleted_at.is_(None))
        .order_by(ExerciseLog.logged_at.desc())
        .limit(limit)
    ).all()

    return [
        RecentLogItem(
            id=row[0].id,
            exercise_slug=row[1],
            exercise_name=row[2],
            metric_type=row[3],
            reps=row[0].reps,
            duration_seconds=row[0].duration_seconds,
            weight_lbs=float(row[0].weight_lbs) if row[0].weight_lbs is not None else None,
            notes=row[0].notes,
            logged_at=row[0].logged_at,
        )
        for row in rows
    ]


def hard_delete_log(db: Session, log_id: int) -> None:
    log = db.scalar(select(ExerciseLog).where(ExerciseLog.id == log_id))
    if not log:
        raise HTTPException(status_code=404, detail="log not found")

    db.delete(log)
    db.commit()
