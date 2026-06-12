from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, JSON, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Workout(Base):
    """Represents a workout definition that can be scheduled and performed.

    Workouts are structured exercise routines composed of multiple steps including
    timed exercises, rest periods, and rep-based exercises. Each workout can be 
    enabled/disabled and ordered for display purposes.
    
    Key Relationships:
        - Workout definitions are stored as JSON structures in the 'definition' field
        - Each workout has a name, duration estimate, and configuration options
    
    Fields:
        - definition: JSON structure containing workout steps (timed exercises, rest periods, etc.)
        - enabled: Boolean flag to control if workout is available for scheduling
        - sort_order: Integer used to order workouts in lists
        - updated_at: Timestamp tracking when the workout definition was last modified
    """
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    definition: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
