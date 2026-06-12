from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExerciseLog(Base):
    """Represents a single instance of an exercise being logged during a workout.

    Exercise logs track the actual performance data for each exercise instance. 
    This allows users to record their workout history and track progress over time.
    
    Key Relationships:
        - Many-to-One relationship with Exercise through exercise_id foreign key
        - Each log entry belongs to exactly one exercise
    
    Fields:
        - reps: Number of repetitions (if applicable for the exercise's metric type)
        - duration_seconds: Duration in seconds (if applicable for the exercise's metric type)  
        - weight_lbs: Weight used in pounds (if applicable for the exercise's metric type)
        - notes: Optional text notes about the specific workout instance
    """
    __tablename__ = "exercise_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), nullable=False, index=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    reps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight_lbs: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    exercise = relationship("Exercise", back_populates="logs")
