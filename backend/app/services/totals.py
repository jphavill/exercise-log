from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.exercise_log import ExerciseLog
from app.schemas.common import Totals


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
