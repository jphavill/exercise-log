from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class TimedExerciseStep(BaseModel):
    kind: Literal["timed_exercise"]
    title: str = Field(min_length=1)
    duration_sec: int = Field(gt=0)


class RestStep(BaseModel):
    kind: Literal["rest"]
    title: str = Field(min_length=1)
    duration_sec: int = Field(gt=0)


class RepExerciseStep(BaseModel):
    kind: Literal["rep_exercise"]
    title: str = Field(min_length=1)
    reps: int = Field(gt=0)
    rep_unit: str = Field(min_length=1)


WorkoutStep = Annotated[TimedExerciseStep | RestStep | RepExerciseStep, Field(discriminator="kind")]


class WorkoutDefinition(BaseModel):
    steps: list[WorkoutStep] = Field(min_length=1)


class WorkoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    duration_min: int
    updated_at: datetime
    steps: list[WorkoutStep]


class WorkoutsResponse(BaseModel):
    workouts: list[WorkoutResponse]


class WorkoutDefinitionResponse(BaseModel):
    id: int
    name: str
    duration_min: int
    enabled: bool
    sort_order: int
    updated_at: datetime
    definition: WorkoutDefinition


class WorkoutDefinitionsResponse(BaseModel):
    workouts: list[WorkoutDefinitionResponse]


class WorkoutCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    enabled: bool = True
    sort_order: int = Field(ge=0)
    definition: WorkoutDefinition


class WorkoutUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    enabled: bool
    sort_order: int = Field(ge=0)
    definition: WorkoutDefinition


class WorkoutEnabledPatchRequest(BaseModel):
    enabled: bool


class ReorderWorkoutItem(BaseModel):
    id: int
    sort_order: int = Field(ge=0)


class ReorderWorkoutsRequest(BaseModel):
    items: list[ReorderWorkoutItem]
