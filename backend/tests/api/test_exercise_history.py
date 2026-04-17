from .helpers import around_training_cutoff_utc_timestamps, cross_day_utc_timestamp, set_log_timestamp


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
    utc_reps = utc_history.json()["days"][0]["totals"]["reps"]
    halifax_reps = halifax_history.json()["days"][0]["totals"]["reps"]
    assert sorted([utc_reps, halifax_reps]) == [0, 5]


def test_history_groups_days_using_3am_training_day_cutoff(client):
    before_cutoff_utc, after_cutoff_utc = around_training_cutoff_utc_timestamps("UTC")

    before = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})
    assert before.status_code == 200
    set_log_timestamp(before.json()["id"], before_cutoff_utc)

    after = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 7})
    assert after.status_code == 200
    set_log_timestamp(after.json()["id"], after_cutoff_utc)

    response = client.get("/api/exercises/pullups/history?days=1", headers={"X-Timezone": "UTC"})
    assert response.status_code == 200
    body = response.json()

    assert body["days"][0]["totals"]["reps"] == 7
    assert body["today_total"]["reps"] == 7
    assert body["last_7_days_total"]["reps"] == 12


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
