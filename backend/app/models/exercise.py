import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MetricType(str, enum.Enum):
    DURATION_SECONDS = "duration_seconds"
    REPS = "reps"
    REPS_PLUS_WEIGHT_LBS = "reps_plus_weight_lbs"


class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint(
            "(goal_reps IS NULL OR goal_reps > 0) AND "
            "(goal_duration_seconds IS NULL OR goal_duration_seconds > 0) AND "
            "(goal_weight_lbs IS NULL OR goal_weight_lbs > 0)",
            name="ck_exercises_goal_positive",
        ),
        CheckConstraint(
            "(" 
            "(goal_reps IS NULL AND goal_duration_seconds IS NULL AND goal_weight_lbs IS NULL) "
            "OR "
            "(metric_type = 'reps' AND goal_reps IS NOT NULL AND goal_duration_seconds IS NULL AND goal_weight_lbs IS NULL) "
            "OR "
            "(metric_type = 'duration_seconds' AND goal_duration_seconds IS NOT NULL AND goal_reps IS NULL AND goal_weight_lbs IS NULL) "
            "OR "
            "(metric_type = 'reps_plus_weight_lbs' AND goal_reps IS NOT NULL AND goal_weight_lbs IS NOT NULL AND goal_duration_seconds IS NULL)"
            ")",
            name="ck_exercises_goal_matches_metric",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_type: Mapped[MetricType] = mapped_column(
        Enum(
            MetricType,
            name="metric_type_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    goal_reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goal_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goal_weight_lbs: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    logs = relationship("ExerciseLog", back_populates="exercise", cascade="all, delete-orphan")
