from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dashboard import ExerciseHistoryResponse
from app.schemas.exercise import (
    ExerciseCreateRequest,
    ExerciseResponse,
    ExerciseUpdateRequest,
    ReorderExercisesRequest,
)
from app.services.dashboard_service import get_exercise_history
from app.services.exercise_service import (
    create_exercise,
    list_exercises,
    reorder_exercises,
    update_exercise,
)

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[ExerciseResponse])
def get_all_exercises(db: Session = Depends(get_db)) -> list[ExerciseResponse]:
    return list_exercises(db)


@router.post("", response_model=ExerciseResponse, status_code=201)
def create_exercise_route(payload: ExerciseCreateRequest, db: Session = Depends(get_db)) -> ExerciseResponse:
    return create_exercise(db, payload)


@router.put("/reorder", response_model=list[ExerciseResponse])
def reorder_exercises_route(
    payload: ReorderExercisesRequest, db: Session = Depends(get_db)
) -> list[ExerciseResponse]:
    return reorder_exercises(db, payload)


@router.put("/{exercise_id}", response_model=ExerciseResponse)
def update_exercise_route(
    exercise_id: int, payload: ExerciseUpdateRequest, db: Session = Depends(get_db)
) -> ExerciseResponse:
    return update_exercise(db, exercise_id, payload)


@router.get("/{slug}/history", response_model=ExerciseHistoryResponse)
def exercise_history(
    slug: str, days: int = Query(default=30, ge=1, le=365), db: Session = Depends(get_db)
) -> ExerciseHistoryResponse:
    return get_exercise_history(db, slug, days)
