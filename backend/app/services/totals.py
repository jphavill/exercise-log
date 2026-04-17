from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.exercise_log import ExerciseLog
from app.schemas.common import Totals
from app.services.shared.progress import grouped_day_expression


def totals_for_exercise(
    db: Session,
    exercise_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
) -> Totals:
    stmt = select(
        func.coalesce(func.sum(ExerciseLog.reps), 0),
        func.coalesce(func.sum(ExerciseLog.duration_seconds), 0),
    ).where(ExerciseLog.exercise_id == exercise_id)

    if start is not None:
        stmt = stmt.where(ExerciseLog.logged_at >= start)
    if end is not None:
        stmt = stmt.where(ExerciseLog.logged_at < end)

    reps, duration = db.execute(stmt).one()
    return Totals(reps=int(reps), duration_seconds=int(duration))


def totals_for_exercise_training_days(
    db: Session,
    exercise_id: int,
    timezone: ZoneInfo,
    start_day: date | None = None,
    end_day_exclusive: date | None = None,
) -> Totals:
    training_day = grouped_day_expression(db, timezone, ExerciseLog.logged_at)
    stmt = select(
        func.coalesce(func.sum(ExerciseLog.reps), 0),
        func.coalesce(func.sum(ExerciseLog.duration_seconds), 0),
    ).where(ExerciseLog.exercise_id == exercise_id)

    if start_day is not None:
        stmt = stmt.where(training_day >= start_day)
    if end_day_exclusive is not None:
        stmt = stmt.where(training_day < end_day_exclusive)

    reps, duration = db.execute(stmt).one()
    return Totals(reps=int(reps), duration_seconds=int(duration))
