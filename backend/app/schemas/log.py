from datetime import datetime

from pydantic import BaseModel, Field

from app.models.exercise import MetricType
from app.schemas.common import Totals


class CreateLogRequest(BaseModel):
    exercise_slug: str
    reps: int | None = Field(default=None, gt=0)
    duration_seconds: int | None = Field(default=None, gt=0)
    weight_lbs: float | None = Field(default=None, gt=0)
    notes: str | None = Field(default=None, max_length=500)


class LogResponse(BaseModel):
    id: int
    exercise_slug: str
    reps: int | None
    duration_seconds: int | None
    weight_lbs: float | None
    logged_at: datetime
    today_total: Totals
    last_7_days_total: Totals


class RecentLogItem(BaseModel):
    id: int
    exercise_slug: str
    exercise_name: str
    metric_type: MetricType
    reps: int | None
    duration_seconds: int | None
    weight_lbs: float | None
    notes: str | None
    logged_at: datetime
