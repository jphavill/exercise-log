from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exercise import Exercise, MetricType
from app.models.workout import Workout

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

DEFAULT_WORKOUTS = [
    {
        "name": "Fingerboard Repeaters",
        "duration_min": 12,
        "definition": {
            "steps": [
                {"kind": "timed_exercise", "title": "20mm crimp", "duration_sec": 20},
                {"kind": "rest", "title": "Rest", "duration_sec": 60},
                {"kind": "timed_exercise", "title": "20mm open hand", "duration_sec": 20},
                {"kind": "rest", "title": "Rest", "duration_sec": 60},
            ]
        },
        "enabled": True,
        "sort_order": 1,
    },
    {
        "name": "Pull-up Ladder",
        "duration_min": 10,
        "definition": {
            "steps": [
                {"kind": "rep_exercise", "title": "Pull-ups", "reps": 5, "rep_unit": "pull-ups"},
                {"kind": "rest", "title": "Rest", "duration_sec": 45},
                {"kind": "rep_exercise", "title": "Pull-ups", "reps": 8, "rep_unit": "pull-ups"},
                {"kind": "rest", "title": "Rest", "duration_sec": 60},
            ]
        },
        "enabled": True,
        "sort_order": 2,
    },
    {
        "name": "Core Compression",
        "duration_min": 8,
        "definition": {
            "steps": [
                {"kind": "timed_exercise", "title": "L-sit hold", "duration_sec": 20},
                {"kind": "rest", "title": "Rest", "duration_sec": 40},
                {"kind": "timed_exercise", "title": "Hollow body hold", "duration_sec": 30},
                {"kind": "rest", "title": "Rest", "duration_sec": 40},
            ]
        },
        "enabled": True,
        "sort_order": 3,
    },
    {
        "name": "Weighted Strength Circuit",
        "duration_min": 20,
        "definition": {
            "steps": [
                {"kind": "rep_exercise", "title": "Weighted pull-ups", "reps": 5, "rep_unit": "reps"},
                {"kind": "rest", "title": "Rest", "duration_sec": 120},
                {"kind": "rep_exercise", "title": "Mace swings", "reps": 20, "rep_unit": "swings"},
                {"kind": "rest", "title": "Rest", "duration_sec": 90},
            ]
        },
        "enabled": True,
        "sort_order": 4,
    },
    {
        "name": "Mobility Reset",
        "duration_min": 15,
        "definition": {
            "steps": [
                {"kind": "timed_exercise", "title": "Wrist prep", "duration_sec": 120},
                {"kind": "timed_exercise", "title": "Shoulder cars", "duration_sec": 90},
                {"kind": "rest", "title": "Breathe", "duration_sec": 30},
                {"kind": "timed_exercise", "title": "Hip openers", "duration_sec": 120},
            ]
        },
        "enabled": True,
        "sort_order": 5,
    },
    {
        "name": "Grip Endurance EMOM",
        "duration_min": 16,
        "definition": {
            "steps": [
                {"kind": "timed_exercise", "title": "Dead hang", "duration_sec": 30},
                {"kind": "rest", "title": "Rest", "duration_sec": 30},
                {"kind": "rep_exercise", "title": "Scap pulls", "reps": 8, "rep_unit": "reps"},
                {"kind": "rest", "title": "Rest", "duration_sec": 45},
            ]
        },
        "enabled": True,
        "sort_order": 6,
    },
]


def seed_exercises(db: Session) -> None:
    existing = {row[0] for row in db.execute(select(Exercise.slug)).all()}
    missing = [Exercise(**exercise) for exercise in DEFAULT_EXERCISES if exercise["slug"] not in existing]
    if missing:
        db.add_all(missing)
        db.commit()


def seed_workouts(db: Session) -> None:
    existing = {row[0] for row in db.execute(select(Workout.name)).all()}
    missing = [Workout(**workout) for workout in DEFAULT_WORKOUTS if workout["name"] not in existing]
    if missing:
        db.add_all(missing)
        db.commit()
