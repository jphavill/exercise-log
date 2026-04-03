from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exercise import Exercise, MetricType

DEFAULT_EXERCISES = [
    {
        "slug": "l-sit",
        "name": "L-sit",
        "metric_type": MetricType.DURATION_SECONDS,
        "sort_order": 1,
        "goal_reps": None,
        "goal_duration_seconds": 40,
        "goal_weight_lbs": None,
    },
    {
        "slug": "pullups",
        "name": "Pull-ups",
        "metric_type": MetricType.REPS,
        "sort_order": 2,
        "goal_reps": 40,
        "goal_duration_seconds": None,
        "goal_weight_lbs": None,
    },
    {
        "slug": "weighted-pullups",
        "name": "Weighted Pull-ups",
        "metric_type": MetricType.REPS_PLUS_WEIGHT_LBS,
        "sort_order": 3,
        "goal_reps": 40,
        "goal_duration_seconds": None,
        "goal_weight_lbs": 15,
    },
    {
        "slug": "mace-swings",
        "name": "Mace Swings",
        "metric_type": MetricType.REPS,
        "sort_order": 4,
        "goal_reps": 40,
        "goal_duration_seconds": None,
        "goal_weight_lbs": None,
    },
]


def seed_exercises(db: Session) -> None:
    existing = {row[0] for row in db.execute(select(Exercise.slug)).all()}
    missing = [Exercise(**exercise) for exercise in DEFAULT_EXERCISES if exercise["slug"] not in existing]
    if missing:
        db.add_all(missing)
        db.commit()
