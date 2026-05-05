from datetime import UTC, datetime

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workout import Workout
from app.schemas.workout import WorkoutDefinition, WorkoutResponse, WorkoutsResponse


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _workout_response(workout: Workout) -> WorkoutResponse:
    try:
        definition = WorkoutDefinition.model_validate(workout.definition)
    except ValidationError as exc:
        raise HTTPException(status_code=500, detail="invalid workout definition") from exc

    return WorkoutResponse.model_validate(
        {
            "id": workout.id,
            "name": workout.name,
            "duration_min": workout.duration_min,
            "updated_at": _ensure_utc(workout.updated_at),
            "steps": definition.steps,
        }
    )


def list_workouts(db: Session) -> WorkoutsResponse:
    workouts = db.scalars(
        select(Workout)
        .where(Workout.enabled.is_(True))
        .order_by(Workout.sort_order, Workout.id)
    ).all()
    return WorkoutsResponse(workouts=[_workout_response(workout) for workout in workouts])
