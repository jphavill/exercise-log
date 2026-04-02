from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.exercise import Exercise
from app.schemas.exercise import (
    ExerciseCreateRequest,
    ExerciseResponse,
    ExerciseUpdateRequest,
    ReorderExercisesRequest,
)


def list_exercises(db: Session) -> list[ExerciseResponse]:
    items = db.scalars(
        select(Exercise)
        .where(Exercise.deleted_at.is_(None))
        .order_by(Exercise.sort_order, Exercise.name)
    ).all()
    return [ExerciseResponse.model_validate(item) for item in items]


def create_exercise(db: Session, payload: ExerciseCreateRequest) -> ExerciseResponse:
    existing = db.scalar(select(Exercise).where(Exercise.slug == payload.slug))
    if existing:
        raise HTTPException(status_code=409, detail="slug already exists")

    exercise = Exercise(
        slug=payload.slug,
        name=payload.name,
        metric_type=payload.metric_type,
        sort_order=payload.sort_order,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return ExerciseResponse.model_validate(exercise)


def update_exercise(db: Session, exercise_id: int, payload: ExerciseUpdateRequest) -> ExerciseResponse:
    exercise = db.scalar(
        select(Exercise).where(and_(Exercise.id == exercise_id, Exercise.deleted_at.is_(None)))
    )
    if not exercise:
        raise HTTPException(status_code=404, detail="exercise not found")

    exercise.name = payload.name
    exercise.metric_type = payload.metric_type
    exercise.sort_order = payload.sort_order

    db.commit()
    db.refresh(exercise)
    return ExerciseResponse.model_validate(exercise)


def reorder_exercises(db: Session, payload: ReorderExercisesRequest) -> list[ExerciseResponse]:
    ids = [item.id for item in payload.items]
    exercises = db.scalars(
        select(Exercise).where(and_(Exercise.id.in_(ids), Exercise.deleted_at.is_(None)))
    ).all()
    if len(exercises) != len(ids):
        raise HTTPException(status_code=404, detail="one or more exercises not found")

    order_map = {item.id: item.sort_order for item in payload.items}
    for exercise in exercises:
        exercise.sort_order = order_map[exercise.id]

    db.commit()
    return list_exercises(db)


def soft_delete_exercise(db: Session, exercise_id: int) -> None:
    exercise = db.scalar(
        select(Exercise).where(and_(Exercise.id == exercise_id, Exercise.deleted_at.is_(None)))
    )
    if not exercise:
        raise HTTPException(status_code=404, detail="exercise not found")

    exercise.deleted_at = datetime.now(UTC)
    db.commit()
