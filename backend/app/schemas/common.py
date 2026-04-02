from pydantic import BaseModel


class Totals(BaseModel):
    reps: int | None = None
    duration_seconds: int | None = None
