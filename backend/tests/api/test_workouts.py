from datetime import UTC, datetime

import pytest
from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.workout import Workout


VALID_STEPS = [
    {"kind": "timed_exercise", "title": "Hang", "duration_sec": 20},
    {"kind": "rest", "title": "Rest", "duration_sec": 60},
    {"kind": "rep_exercise", "title": "Pull-ups", "reps": 10, "rep_unit": "pull-ups"},
]


def _replace_workouts(workouts: list[Workout]) -> None:
    with SessionLocal() as db:
        db.execute(delete(Workout))
        db.add_all(workouts)
        db.commit()


def _workout(name: str, *, sort_order: int, enabled: bool = True, steps: list[dict] | None = None) -> Workout:
    return Workout(
        name=name,
        duration_min=12,
        definition={"steps": steps or VALID_STEPS},
        enabled=enabled,
        sort_order=sort_order,
        updated_at=datetime(2026, 5, 4, 20, 0, tzinfo=UTC),
    )


def test_get_workouts_returns_enabled_workouts_ordered_by_sort_order_then_id(client):
    _replace_workouts(
        [
            _workout("Second Sort", sort_order=2),
            _workout("First Sort A", sort_order=1),
            _workout("Disabled", sort_order=0, enabled=False),
            _workout("First Sort B", sort_order=1),
        ]
    )

    response = client.get("/api/workouts")

    assert response.status_code == 200
    workouts = response.json()["workouts"]
    assert [workout["name"] for workout in workouts] == ["First Sort A", "First Sort B", "Second Sort"]
    assert "Disabled" not in {workout["name"] for workout in workouts}


def test_get_workouts_response_has_required_fields_and_steps(client):
    response = client.get("/api/workouts")

    assert response.status_code == 200
    workouts = response.json()["workouts"]
    assert len(workouts) == 6
    first = workouts[0]
    assert {"id", "name", "duration_min", "updated_at", "steps"}.issubset(first)
    assert first["steps"]

    step_kinds = {step["kind"] for workout in workouts for step in workout["steps"]}
    assert {"timed_exercise", "rest", "rep_exercise"}.issubset(step_kinds)


@pytest.mark.parametrize(
    "step",
    [
        {"kind": "timed_exercise", "title": "Hang"},
        {"kind": "rest", "title": "Rest"},
        {"kind": "rep_exercise", "title": "Pull-ups", "rep_unit": "pull-ups"},
        {"kind": "rep_exercise", "title": "Pull-ups", "reps": 10},
        {"kind": "unknown", "title": "Mystery", "duration_sec": 10},
    ],
)
def test_get_workouts_rejects_invalid_step_definitions(client, step):
    _replace_workouts([_workout("Invalid", sort_order=1, steps=[step])])

    response = client.get("/api/workouts")

    assert response.status_code == 500
    assert response.json()["detail"] == "invalid workout definition"
