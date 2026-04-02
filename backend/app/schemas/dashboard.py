from datetime import date

from pydantic import BaseModel

from app.models.exercise import MetricType
from app.schemas.common import Totals
from app.schemas.log import RecentLogItem


class ExerciseTotalsItem(BaseModel):
    exercise_id: int
    exercise_slug: str
    exercise_name: str
    metric_type: MetricType
    totals: Totals


class DashboardSummaryResponse(BaseModel):
    today: list[ExerciseTotalsItem]
    current_week: list[ExerciseTotalsItem]
    last_30_days: list[ExerciseTotalsItem]
    total_logs_today: int
    total_logs_this_week: int


class DailyTotalItem(BaseModel):
    day: date
    totals: Totals


class BestDay(BaseModel):
    day: date
    totals: Totals


class ExerciseMeta(BaseModel):
    id: int
    slug: str
    name: str
    metric_type: MetricType


class ExerciseHistoryResponse(BaseModel):
    exercise: ExerciseMeta
    days: list[DailyTotalItem]
    current_streak: int
    best_day: BestDay | None
    all_time_total: Totals
    today_total: Totals
    last_7_days_total: Totals
    last_30_days_total: Totals
    recent_logs: list[RecentLogItem]
