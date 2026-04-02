from pydantic import BaseModel, ConfigDict, Field, field_validator
from slugify import slugify

from app.models.exercise import MetricType


class ExerciseBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    metric_type: MetricType
    sort_order: int = Field(gt=0)


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


class ReorderExerciseItem(BaseModel):
    id: int
    sort_order: int = Field(gt=0)


class ReorderExercisesRequest(BaseModel):
    items: list[ReorderExerciseItem]
