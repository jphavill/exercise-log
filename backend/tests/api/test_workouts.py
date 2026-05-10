from datetime import UTC, datetime
import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import delete, select

from app.db.session import SessionLocal, engine
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


def test_get_workout_returns_specific_enabled_workout(client):
    _replace_workouts(
        [
            _workout("First", sort_order=1),
            _workout("Target", sort_order=2),
        ]
    )
    list_response = client.get("/api/workouts")
    target_id = next(workout["id"] for workout in list_response.json()["workouts"] if workout["name"] == "Target")

    response = client.get(f"/api/workouts/{target_id}")

    assert response.status_code == 200
    workout = response.json()
    assert workout["id"] == target_id
    assert workout["name"] == "Target"
    assert workout["steps"] == VALID_STEPS


def test_get_workout_returns_404_for_missing_or_disabled_workout(client):
    _replace_workouts([_workout("Disabled", sort_order=1, enabled=False)])
    assert client.get("/api/workouts").json()["workouts"] == []

    assert client.get("/api/workouts/999999").status_code == 404

    with SessionLocal() as db:
        workout_id = db.scalar(select(Workout.id).where(Workout.name == "Disabled"))

    assert workout_id is not None
    assert client.get(f"/api/workouts/{workout_id}").status_code == 404


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


def test_get_workout_definitions_include_disabled_workouts(client):
    _replace_workouts(
        [
            _workout("Enabled", sort_order=2),
            _workout("Disabled", sort_order=1, enabled=False),
        ]
    )

    response = client.get("/api/workouts?include_disabled=true&detail=definition")

    assert response.status_code == 200
    workouts = response.json()["workouts"]
    assert [workout["name"] for workout in workouts] == ["Disabled", "Enabled"]
    disabled = workouts[0]
    assert disabled["enabled"] is False
    assert disabled["sort_order"] == 1
    assert disabled["updated_at"]
    assert disabled["definition"] == {"steps": VALID_STEPS}
    assert "steps" not in disabled


def test_get_disabled_workout_definition_by_id_with_editor_params(client):
    _replace_workouts([_workout("Disabled", sort_order=1, enabled=False)])
    with SessionLocal() as db:
        workout_id = db.scalar(select(Workout.id).where(Workout.name == "Disabled"))

    response = client.get(f"/api/workouts/{workout_id}?include_disabled=true&detail=definition")

    assert response.status_code == 200
    workout = response.json()
    assert workout["id"] == workout_id
    assert workout["enabled"] is False
    assert workout["definition"] == {"steps": VALID_STEPS}


def test_create_workout_calculates_duration_from_timed_and_rest_steps(client):
    payload = {
        "name": "Created",
        "enabled": False,
        "sort_order": 8,
        "definition": {
            "steps": [
                {"kind": "timed_exercise", "title": "Hang", "duration_sec": 61},
                {"kind": "rest", "title": "Rest", "duration_sec": 30},
                {"kind": "rep_exercise", "title": "Pull-ups", "reps": 10, "rep_unit": "reps"},
            ]
        },
    }

    response = client.post("/api/workouts", json=payload)

    assert response.status_code == 201
    workout = response.json()
    assert workout["name"] == "Created"
    assert workout["enabled"] is False
    assert workout["sort_order"] == 8
    assert workout["duration_min"] == 2
    assert workout["definition"] == payload["definition"]


def test_create_workout_rejects_invalid_definitions(client):
    response = client.post(
        "/api/workouts",
        json={
            "name": "Invalid",
            "enabled": True,
            "sort_order": 1,
            "definition": {"steps": []},
        },
    )

    assert response.status_code == 422


def test_update_workout_replaces_editable_fields_and_recalculates_duration(client):
    _replace_workouts([_workout("Original", sort_order=1)])
    with SessionLocal() as db:
        workout_id = db.scalar(select(Workout.id).where(Workout.name == "Original"))
    payload = {
        "name": "Updated",
        "enabled": False,
        "sort_order": 4,
        "definition": {
            "steps": [
                {"kind": "timed_exercise", "title": "Hang", "duration_sec": 120},
                {"kind": "rest", "title": "Rest", "duration_sec": 1},
            ]
        },
    }

    response = client.put(f"/api/workouts/{workout_id}", json=payload)

    assert response.status_code == 200
    workout = response.json()
    assert workout["name"] == "Updated"
    assert workout["enabled"] is False
    assert workout["sort_order"] == 4
    assert workout["duration_min"] == 3
    assert workout["definition"] == payload["definition"]


def test_update_workout_rejects_missing_workout(client):
    response = client.put(
        "/api/workouts/999999",
        json={
            "name": "Missing",
            "enabled": True,
            "sort_order": 1,
            "definition": {"steps": VALID_STEPS},
        },
    )

    assert response.status_code == 404


def test_patch_workout_enabled_toggles_enabled_and_updates_timestamp(client):
    _replace_workouts([_workout("Toggle", sort_order=1, enabled=False)])
    with SessionLocal() as db:
        workout = db.scalar(select(Workout).where(Workout.name == "Toggle"))
        assert workout is not None
        workout_id = workout.id
        previous_updated_at = workout.updated_at

    response = client.patch(f"/api/workouts/{workout_id}/enabled", json={"enabled": True})

    assert response.status_code == 200
    assert response.json()["enabled"] is True
    with SessionLocal() as db:
        updated = db.get(Workout, workout_id)
        assert updated is not None
        assert updated.enabled is True
        assert updated.updated_at > previous_updated_at


def test_reorder_workouts_persists_sort_order_and_returns_ordered_workouts(client):
    _replace_workouts(
        [
            _workout("A", sort_order=1),
            _workout("B", sort_order=2),
            _workout("C", sort_order=3, enabled=False),
        ]
    )
    with SessionLocal() as db:
        ids = dict(db.execute(select(Workout.name, Workout.id)).all())

    response = client.put(
        "/api/workouts/reorder",
        json={
            "items": [
                {"id": ids["C"], "sort_order": 1},
                {"id": ids["A"], "sort_order": 2},
                {"id": ids["B"], "sort_order": 3},
            ]
        },
    )

    assert response.status_code == 200
    workouts = response.json()["workouts"]
    assert [workout["name"] for workout in workouts] == ["C", "A", "B"]
    with SessionLocal() as db:
        stored = dict(db.execute(select(Workout.name, Workout.sort_order)).all())
    assert stored == {"A": 2, "B": 3, "C": 1}


def test_delete_workout_hard_deletes_workout(client):
    _replace_workouts([_workout("Delete Me", sort_order=1)])
    with SessionLocal() as db:
        workout_id = db.scalar(select(Workout.id).where(Workout.name == "Delete Me"))

    response = client.delete(f"/api/workouts/{workout_id}")

    assert response.status_code == 204
    with SessionLocal() as db:
        assert db.get(Workout, workout_id) is None


def test_delete_workout_rejects_missing_workout(client):
    assert client.delete("/api/workouts/999999").status_code == 404


def test_duration_recalculation_migration_updates_existing_rows(monkeypatch):
    _replace_workouts(
        [
            _workout(
                "Timed",
                sort_order=1,
                steps=[
                    {"kind": "timed_exercise", "title": "Hang", "duration_sec": 61},
                    {"kind": "rest", "title": "Rest", "duration_sec": 30},
                ],
            ),
            _workout(
                "Reps Only",
                sort_order=2,
                steps=[{"kind": "rep_exercise", "title": "Pull-ups", "reps": 10, "rep_unit": "reps"}],
            ),
        ]
    )

    migration_path = (
        Path(__file__).resolve().parents[2]
        / "alembic"
        / "versions"
        / "0006_recalculate_durations.py"
    )
    spec = importlib.util.spec_from_file_location("recalculate_workout_durations", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with engine.begin() as connection:
        monkeypatch.setattr(migration.op, "get_bind", lambda: connection)
        migration.upgrade()

    with SessionLocal() as db:
        durations = dict(db.execute(select(Workout.name, Workout.duration_min)).all())

    assert durations["Timed"] == 2
    assert durations["Reps Only"] == 1
