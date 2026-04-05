from .helpers import cross_day_utc_timestamp, set_log_timestamp


def test_valid_pullup_log_creation(client):
    response = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["exercise_slug"] == "pullups"
    assert body["reps"] == 5
    assert body["today_total"]["reps"] == 5


def test_valid_weighted_pullup_log_creation(client):
    response = client.post(
        "/api/logs",
        json={"exercise_slug": "weighted-pullups", "reps": 3, "weight_lbs": 25},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reps"] == 3
    assert body["weight_lbs"] == 25


def test_valid_l_sit_log_creation(client):
    response = client.post("/api/logs", json={"exercise_slug": "l-sit", "duration_seconds": 20})
    assert response.status_code == 200
    body = response.json()
    assert body["duration_seconds"] == 20
    assert body["today_total"]["duration_seconds"] == 20


def test_valid_mace_swings_log_creation(client):
    response = client.post("/api/logs", json={"exercise_slug": "mace-swings", "reps": 20})
    assert response.status_code == 200
    assert response.json()["reps"] == 20


def test_invalid_metric_combination(client):
    response = client.post(
        "/api/logs",
        json={"exercise_slug": "pullups", "reps": 5, "weight_lbs": 20},
    )
    assert response.status_code == 422


def test_invalid_slug(client):
    response = client.post("/api/logs", json={"exercise_slug": "does-not-exist", "reps": 5})
    assert response.status_code == 404


def test_recent_logs_limit_bounds(client):
    ok_response = client.get("/api/logs/recent?limit=200")
    assert ok_response.status_code == 200

    invalid_response = client.get("/api/logs/recent?limit=201")
    assert invalid_response.status_code == 422


def test_delete_log_hard_delete_removes_individual_entry(client):
    create_response = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})
    assert create_response.status_code == 200
    log_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/logs/{log_id}")
    assert delete_response.status_code == 204

    recent = client.get("/api/logs/recent?limit=20")
    assert recent.status_code == 200
    remaining_ids = {item["id"] for item in recent.json()}
    assert log_id not in remaining_ids


def test_delete_missing_log_returns_404(client):
    response = client.delete("/api/logs/999999")
    assert response.status_code == 404


def test_deleted_exercise_cannot_create_logs(client):
    exercises = client.get("/api/exercises").json()
    target = exercises[0]

    delete_response = client.delete(f"/api/exercises/{target['id']}")
    assert delete_response.status_code == 204

    payload = {"exercise_slug": target["slug"], "reps": 5}
    if target["metric_type"] == "duration_seconds":
        payload = {"exercise_slug": target["slug"], "duration_seconds": 20}
    elif target["metric_type"] == "reps_plus_weight_lbs":
        payload = {"exercise_slug": target["slug"], "reps": 5, "weight_lbs": 25}

    response = client.post("/api/logs", json=payload)
    assert response.status_code == 404


def test_create_log_uses_request_timezone_for_today_totals(client):
    create_response = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})
    assert create_response.status_code == 200
    boundary_log_id = create_response.json()["id"]
    set_log_timestamp(boundary_log_id, cross_day_utc_timestamp("America/Halifax"))

    utc_response = client.post(
        "/api/logs",
        json={"exercise_slug": "pullups", "reps": 1},
        headers={"X-Timezone": "UTC"},
    )
    assert utc_response.status_code == 200
    utc_body = utc_response.json()
    assert utc_body["today_total"]["reps"] == 1

    client.delete(f"/api/logs/{utc_body['id']}")

    halifax_response = client.post(
        "/api/logs",
        json={"exercise_slug": "pullups", "reps": 1},
        headers={"X-Timezone": "America/Halifax"},
    )
    assert halifax_response.status_code == 200
    assert halifax_response.json()["today_total"]["reps"] == 6


def test_create_log_invalid_timezone_falls_back_to_utc(client):
    create_response = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})
    assert create_response.status_code == 200
    set_log_timestamp(create_response.json()["id"], cross_day_utc_timestamp("America/Halifax"))

    invalid_tz_response = client.post(
        "/api/logs",
        json={"exercise_slug": "pullups", "reps": 1},
        headers={"X-Timezone": "Not/A_Real_Zone"},
    )
    assert invalid_tz_response.status_code == 200

    utc_response = client.post(
        "/api/logs",
        json={"exercise_slug": "pullups", "reps": 1},
        headers={"X-Timezone": "UTC"},
    )
    assert utc_response.status_code == 200

    assert invalid_tz_response.json()["today_total"]["reps"] == utc_response.json()["today_total"]["reps"] - 1


def test_create_log_missing_timezone_defaults_to_utc(client):
    no_header_response = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 1})
    assert no_header_response.status_code == 200

    utc_response = client.post(
        "/api/logs",
        json={"exercise_slug": "pullups", "reps": 1},
        headers={"X-Timezone": "UTC"},
    )
    assert utc_response.status_code == 200
    assert no_header_response.json()["today_total"]["reps"] == utc_response.json()["today_total"]["reps"] - 1
