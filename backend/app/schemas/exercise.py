from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from slugify import slugify

from app.models.exercise import MetricType


class ExerciseBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    metric_type: MetricType
    sort_order: int = Field(gt=0)
    goal_reps: int | None = Field(default=None, gt=0)
    goal_duration_seconds: int | None = Field(default=None, gt=0)
    goal_weight_lbs: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_goal_by_metric(self) -> "ExerciseBase":
        if (
            self.goal_reps is None
            and self.goal_duration_seconds is None
            and self.goal_weight_lbs is None
        ):
            return self

        if self.metric_type == MetricType.REPS:
            if self.goal_reps is None:
                raise ValueError("reps exercises require goal_reps")
            if self.goal_duration_seconds is not None or self.goal_weight_lbs is not None:
                raise ValueError("reps exercises only allow goal_reps")
        elif self.metric_type == MetricType.DURATION_SECONDS:
            if self.goal_duration_seconds is None:
                raise ValueError("duration_seconds exercises require goal_duration_seconds")
            if self.goal_reps is not None or self.goal_weight_lbs is not None:
                raise ValueError("duration_seconds exercises only allow goal_duration_seconds")
        elif self.metric_type == MetricType.REPS_PLUS_WEIGHT_LBS:
            if self.goal_reps is None or self.goal_weight_lbs is None:
                raise ValueError("reps_plus_weight_lbs exercises require goal_reps and goal_weight_lbs")
            if self.goal_duration_seconds is not None:
                raise ValueError("reps_plus_weight_lbs exercises do not allow goal_duration_seconds")
        return self


class ExerciseCreateRequest(ExerciseBase):
    slug: str = Field(min_length=1, max_length=100)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        normalized = slugify(value)
        if normalized != value:
            raise ValueError("slug must be URL-safe lowercase text")
        return value


class ExerciseUpdateRequest(ExerciseBase):
    pass


class ExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    metric_type: MetricType
    sort_order: int
    goal_reps: int | None
    goal_duration_seconds: int | None
    goal_weight_lbs: float | None


class ReorderExerciseItem(BaseModel):
    id: int
    sort_order: int = Field(gt=0)


class ReorderExercisesRequest(BaseModel):
    items: list[ReorderExerciseItem]
