import enum

from sqlalchemy import Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MetricType(str, enum.Enum):
    DURATION_SECONDS = "duration_seconds"
    REPS = "reps"
    REPS_PLUS_WEIGHT_LBS = "reps_plus_weight_lbs"


class Exercise(Base):
    __tablename__ = "exercises"

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

    logs = relationship("ExerciseLog", back_populates="exercise", cascade="all, delete-orphan")
