from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exercise import Exercise, MetricType

DEFAULT_EXERCISES = [
    {
        "slug": "l-sit",
        "name": "L-sit",
        "metric_type": MetricType.DURATION_SECONDS,
        "sort_order": 1,
    },
    {
        "slug": "pullups",
        "name": "Pull-ups",
        "metric_type": MetricType.REPS,
        "sort_order": 2,
    },
    {
        "slug": "weighted-pullups",
        "name": "Weighted Pull-ups",
        "metric_type": MetricType.REPS_PLUS_WEIGHT_LBS,
        "sort_order": 3,
    },
    {
        "slug": "mace-swings",
        "name": "Mace Swings",
        "metric_type": MetricType.REPS,
        "sort_order": 4,
    },
]


def seed_exercises(db: Session) -> None:
    existing = {row[0] for row in db.execute(select(Exercise.slug)).all()}
    missing = [Exercise(**exercise) for exercise in DEFAULT_EXERCISES if exercise["slug"] not in existing]
    if missing:
        db.add_all(missing)
        db.commit()
