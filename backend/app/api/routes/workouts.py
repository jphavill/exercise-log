from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.workout import WorkoutsResponse
from app.services.workout_service import list_workouts

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("", response_model=WorkoutsResponse)
def get_workouts(db: Session = Depends(get_db)) -> WorkoutsResponse:
    return list_workouts(db)
