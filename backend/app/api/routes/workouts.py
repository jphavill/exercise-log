from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.workout import (
    ReorderWorkoutsRequest,
    WorkoutCreateRequest,
    WorkoutDefinitionResponse,
    WorkoutDefinitionsResponse,
    WorkoutEnabledPatchRequest,
    WorkoutResponse,
    WorkoutsResponse,
    WorkoutUpdateRequest,
)
from app.services.workout_service import (
    create_workout,
    delete_workout,
    get_workout_row,
    list_workout_rows,
    reorder_workouts,
    set_workout_enabled,
    to_workout_definition_response,
    to_workout_summary_response,
    update_workout,
)

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("", response_model=WorkoutsResponse | WorkoutDefinitionsResponse)
def get_workouts(
    db: Session = Depends(get_db),
    include_disabled: bool = Query(False),
    detail: Literal["summary", "definition"] = Query("summary"),
) -> WorkoutsResponse | WorkoutDefinitionsResponse:
    rows = list_workout_rows(db, include_disabled=include_disabled)
    if detail == "definition":
        return WorkoutDefinitionsResponse(
            workouts=[to_workout_definition_response(row) for row in rows]
        )
    return WorkoutsResponse(workouts=[to_workout_summary_response(row) for row in rows])


@router.post("", response_model=WorkoutDefinitionResponse, status_code=201)
def create_workout_route(
    payload: WorkoutCreateRequest, db: Session = Depends(get_db)
) -> WorkoutDefinitionResponse:
    return to_workout_definition_response(create_workout(db, payload))


@router.put("/reorder", response_model=WorkoutDefinitionsResponse)
def reorder_workouts_route(
    payload: ReorderWorkoutsRequest, db: Session = Depends(get_db)
) -> WorkoutDefinitionsResponse:
    rows = reorder_workouts(db, payload)
    return WorkoutDefinitionsResponse(workouts=[to_workout_definition_response(row) for row in rows])


@router.get("/{workout_id}", response_model=WorkoutResponse | WorkoutDefinitionResponse)
def get_workout_by_id(
    workout_id: int,
    db: Session = Depends(get_db),
    include_disabled: bool = Query(False),
    detail: Literal["summary", "definition"] = Query("summary"),
) -> WorkoutResponse | WorkoutDefinitionResponse:
    row = get_workout_row(db, workout_id, include_disabled=include_disabled)
    if detail == "definition":
        return to_workout_definition_response(row)
    return to_workout_summary_response(row)


@router.put("/{workout_id}", response_model=WorkoutDefinitionResponse)
def update_workout_route(
    workout_id: int, payload: WorkoutUpdateRequest, db: Session = Depends(get_db)
) -> WorkoutDefinitionResponse:
    return to_workout_definition_response(update_workout(db, workout_id, payload))


@router.patch("/{workout_id}/enabled", response_model=WorkoutDefinitionResponse)
def set_workout_enabled_route(
    workout_id: int, payload: WorkoutEnabledPatchRequest, db: Session = Depends(get_db)
) -> WorkoutDefinitionResponse:
    return to_workout_definition_response(set_workout_enabled(db, workout_id, payload.enabled))


@router.delete("/{workout_id}", status_code=204)
def delete_workout_route(workout_id: int, db: Session = Depends(get_db)) -> None:
    delete_workout(db, workout_id)
