from datetime import UTC, datetime
from math import ceil

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workout import Workout
from app.schemas.workout import (
    ReorderWorkoutsRequest,
    WorkoutCreateRequest,
    WorkoutDefinition,
    WorkoutDefinitionResponse,
    WorkoutResponse,
    WorkoutUpdateRequest,
)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def calculate_duration_min(definition: WorkoutDefinition) -> int:
    total_seconds = sum(
        step.duration_sec
        for step in definition.steps
        if step.kind in {"timed_exercise", "rest"}
    )
    return max(1, ceil(total_seconds / 60))


def _validated_definition(workout: Workout) -> WorkoutDefinition:
    try:
        return WorkoutDefinition.model_validate(workout.definition)
    except ValidationError as exc:
        raise HTTPException(status_code=500, detail="invalid workout definition") from exc


def list_workout_rows(db: Session, include_disabled: bool) -> list[Workout]:
    stmt = select(Workout)
    if not include_disabled:
        stmt = stmt.where(Workout.enabled.is_(True))
    return list(db.scalars(stmt.order_by(Workout.sort_order, Workout.id)).all())


def get_workout_row(db: Session, workout_id: int, include_disabled: bool = False) -> Workout:
    stmt = select(Workout).where(Workout.id == workout_id)
    if not include_disabled:
        stmt = stmt.where(Workout.enabled.is_(True))

    workout = db.scalar(stmt)
    if workout is None:
        raise HTTPException(status_code=404, detail="workout not found")
    return workout


def create_workout(db: Session, payload: WorkoutCreateRequest) -> Workout:
    now = datetime.now(UTC)
    workout = Workout(
        name=payload.name,
        duration_min=calculate_duration_min(payload.definition),
        definition=payload.definition.model_dump(mode="json"),
        enabled=payload.enabled,
        sort_order=payload.sort_order,
        updated_at=now,
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout


def update_workout(db: Session, workout_id: int, payload: WorkoutUpdateRequest) -> Workout:
    workout = get_workout_row(db, workout_id, include_disabled=True)
    workout.name = payload.name
    workout.duration_min = calculate_duration_min(payload.definition)
    workout.definition = payload.definition.model_dump(mode="json")
    workout.enabled = payload.enabled
    workout.sort_order = payload.sort_order
    workout.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(workout)
    return workout


def set_workout_enabled(db: Session, workout_id: int, enabled: bool) -> Workout:
    workout = get_workout_row(db, workout_id, include_disabled=True)
    workout.enabled = enabled
    workout.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(workout)
    return workout


def reorder_workouts(db: Session, payload: ReorderWorkoutsRequest) -> list[Workout]:
    ids = [item.id for item in payload.items]
    workouts = list(db.scalars(select(Workout).where(Workout.id.in_(ids))).all())
    if len(workouts) != len(set(ids)) or len(ids) != len(set(ids)):
        raise HTTPException(status_code=404, detail="one or more workouts not found")

    now = datetime.now(UTC)
    order_map = {item.id: item.sort_order for item in payload.items}
    for workout in workouts:
        workout.sort_order = order_map[workout.id]
        workout.updated_at = now

    db.commit()
    return list_workout_rows(db, include_disabled=True)


def delete_workout(db: Session, workout_id: int) -> None:
    workout = get_workout_row(db, workout_id, include_disabled=True)
    db.delete(workout)
    db.commit()


def to_workout_summary_response(workout: Workout) -> WorkoutResponse:
    definition = _validated_definition(workout)
    return WorkoutResponse.model_validate(
        {
            "id": workout.id,
            "name": workout.name,
            "duration_min": workout.duration_min,
            "updated_at": _ensure_utc(workout.updated_at),
            "steps": definition.steps,
        }
    )


def to_workout_definition_response(workout: Workout) -> WorkoutDefinitionResponse:
    return WorkoutDefinitionResponse.model_validate(
        {
            "id": workout.id,
            "name": workout.name,
            "duration_min": workout.duration_min,
            "enabled": workout.enabled,
            "sort_order": workout.sort_order,
            "updated_at": _ensure_utc(workout.updated_at),
            "definition": _validated_definition(workout),
        }
    )
