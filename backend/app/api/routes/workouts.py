from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.workout import WorkoutResponse, WorkoutsResponse
from app.services.workout_service import get_workout, list_workouts

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("", response_model=WorkoutsResponse)
def get_workouts(db: Session = Depends(get_db)) -> WorkoutsResponse:
    return list_workouts(db)


@router.get("/{workout_id}", response_model=WorkoutResponse)
def get_workout_by_id(workout_id: int, db: Session = Depends(get_db)) -> WorkoutResponse:
    return get_workout(db, workout_id)
