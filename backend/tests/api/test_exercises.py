from .helpers import cross_day_utc_timestamp, set_log_timestamp


def test_history_endpoint_output(client):
    client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 4})
    response = client.get("/api/exercises/pullups/history?days=30")
    assert response.status_code == 200
    body = response.json()
    assert body["exercise"]["slug"] == "pullups"
    assert len(body["days"]) == 30
    assert "current_streak" in body
    assert body["exercise"]["goal_reps"] == 40


def test_history_endpoint_invalid_days_range(client):
    zero_day_response = client.get("/api/exercises/pullups/history?days=0")
    assert zero_day_response.status_code == 422

    too_large_response = client.get("/api/exercises/pullups/history?days=366")
    assert too_large_response.status_code == 422


def test_history_endpoint_missing_slug_returns_404(client):
    response = client.get("/api/exercises/not-a-real-exercise/history?days=30")
    assert response.status_code == 404


def test_history_uses_request_timezone_for_day_bucket(client):
    create_response = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})
    assert create_response.status_code == 200
    set_log_timestamp(create_response.json()["id"], cross_day_utc_timestamp("America/Halifax"))

    utc_history = client.get("/api/exercises/pullups/history?days=1", headers={"X-Timezone": "UTC"})
    halifax_history = client.get(
        "/api/exercises/pullups/history?days=1",
        headers={"X-Timezone": "America/Halifax"},
    )

    assert utc_history.status_code == 200
    assert halifax_history.status_code == 200
    assert utc_history.json()["days"][0]["totals"]["reps"] == 0
    assert halifax_history.json()["days"][0]["totals"]["reps"] == 5


def test_history_invalid_timezone_falls_back_to_utc(client):
    create_response = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})
    assert create_response.status_code == 200
    set_log_timestamp(create_response.json()["id"], cross_day_utc_timestamp("America/Halifax"))

    invalid_response = client.get(
        "/api/exercises/pullups/history?days=1",
        headers={"X-Timezone": "Not/A_Real_Zone"},
    )
    utc_response = client.get("/api/exercises/pullups/history?days=1", headers={"X-Timezone": "UTC"})

    assert invalid_response.status_code == 200
    assert utc_response.status_code == 200
    assert invalid_response.json()["days"][0]["totals"]["reps"] == utc_response.json()["days"][0]["totals"]["reps"]


def test_create_exercise_endpoint(client):
    response = client.post(
        "/api/exercises",
        json={
            "slug": "dead-hang",
            "name": "Dead Hang",
            "metric_type": "duration_seconds",
            "sort_order": 5,
            "goal_reps": None,
            "goal_duration_seconds": 40,
            "goal_weight_lbs": None,
        },
    )
    assert response.status_code == 201
    assert response.json()["slug"] == "dead-hang"


def test_create_exercise_duplicate_slug_returns_409(client):
    response = client.post(
        "/api/exercises",
        json={
            "slug": "pullups",
            "name": "Pullups Duplicate",
            "metric_type": "reps",
            "sort_order": 5,
            "goal_reps": 20,
            "goal_duration_seconds": None,
            "goal_weight_lbs": None,
        },
    )
    assert response.status_code == 409


def test_create_exercise_invalid_slug_returns_422(client):
    response = client.post(
        "/api/exercises",
        json={
            "slug": "Upper Case",
            "name": "Upper Case",
            "metric_type": "reps",
            "sort_order": 5,
            "goal_reps": 20,
            "goal_duration_seconds": None,
            "goal_weight_lbs": None,
        },
    )
    assert response.status_code == 422


def test_weighted_history_goal_progress_uses_goal_weight_or_higher(client):
    client.post("/api/logs", json={"exercise_slug": "weighted-pullups", "reps": 4, "weight_lbs": 10})
    client.post("/api/logs", json={"exercise_slug": "weighted-pullups", "reps": 6, "weight_lbs": 15})
    client.post("/api/logs", json={"exercise_slug": "weighted-pullups", "reps": 8, "weight_lbs": 20})

    response = client.get("/api/exercises/weighted-pullups/history?days=1")
    assert response.status_code == 200
    body = response.json()
    assert body["exercise"]["goal_reps"] == 40
    assert body["exercise"]["goal_weight_lbs"] == 15
    assert body["days"][0]["totals"]["reps"] == 18
    assert body["days"][0]["goal_progress_value"] == 14


def test_update_exercise_endpoint(client):
    exercises = client.get("/api/exercises").json()
    target = exercises[0]

    response = client.put(
        f"/api/exercises/{target['id']}",
        json={
            "name": "Updated Name",
            "metric_type": target["metric_type"],
            "sort_order": 9,
            "goal_reps": target["goal_reps"],
            "goal_duration_seconds": target["goal_duration_seconds"],
            "goal_weight_lbs": target["goal_weight_lbs"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Updated Name"
    assert body["sort_order"] == 9


def test_update_exercise_endpoint_missing_exercise_returns_404(client):
    response = client.put(
        "/api/exercises/999999",
        json={
            "name": "Updated Name",
            "metric_type": "reps",
            "sort_order": 9,
            "goal_reps": 10,
            "goal_duration_seconds": None,
            "goal_weight_lbs": None,
        },
    )
    assert response.status_code == 404


def test_update_exercise_endpoint_allows_clearing_goal(client):
    exercises = client.get("/api/exercises").json()
    target = exercises[0]

    response = client.put(
        f"/api/exercises/{target['id']}",
        json={
            "name": target["name"],
            "metric_type": target["metric_type"],
            "sort_order": target["sort_order"],
            "goal_reps": None,
            "goal_duration_seconds": None,
            "goal_weight_lbs": None,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["goal_reps"] is None
    assert body["goal_duration_seconds"] is None
    assert body["goal_weight_lbs"] is None


def test_reorder_exercises_endpoint(client):
    exercises = client.get("/api/exercises").json()
    payload = {
        "items": [
            {"id": exercises[0]["id"], "sort_order": 3},
            {"id": exercises[1]["id"], "sort_order": 1},
            {"id": exercises[2]["id"], "sort_order": 4},
            {"id": exercises[3]["id"], "sort_order": 2},
        ]
    }
    response = client.put("/api/exercises/reorder", json=payload)
    assert response.status_code == 200
    orders = {item["id"]: item["sort_order"] for item in response.json()}
    assert orders[exercises[0]["id"]] == 3
    assert orders[exercises[1]["id"]] == 1


def test_reorder_exercises_endpoint_missing_item_returns_404(client):
    payload = {"items": [{"id": 999999, "sort_order": 1}]}
    response = client.put("/api/exercises/reorder", json=payload)
    assert response.status_code == 404


def test_delete_exercise_soft_delete_hides_from_list(client):
    exercises = client.get("/api/exercises").json()
    target = exercises[0]

    response = client.delete(f"/api/exercises/{target['id']}")
    assert response.status_code == 204

    remaining = client.get("/api/exercises").json()
    remaining_ids = {item["id"] for item in remaining}
    assert target["id"] not in remaining_ids
