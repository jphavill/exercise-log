from datetime import date

from pydantic import BaseModel


class PullupsWidgetDayItem(BaseModel):
    date: date
    count: int
    heat_level: int


class PullupsWidgetResponse(BaseModel):
    year_total: int
    daily_goal: int | None
    last_30_days: list[PullupsWidgetDayItem]
