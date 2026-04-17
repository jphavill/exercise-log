from .helpers import around_training_cutoff_utc_timestamps, cross_day_utc_timestamp, set_log_timestamp


def test_dashboard_summary_output(client):
    client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})
    client.post("/api/logs", json={"exercise_slug": "l-sit", "duration_seconds": 15})

    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert "today" in body
    assert "current_week" in body
    assert "last_30_days_consistency" in body
    assert body["total_logs_today"] >= 2


def test_dashboard_summary_uses_request_timezone_for_day_bucket(client):
    create_response = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})
    assert create_response.status_code == 200
    log_id = create_response.json()["id"]
    set_log_timestamp(log_id, cross_day_utc_timestamp("America/Halifax"))

    utc_summary = client.get("/api/dashboard/summary", headers={"X-Timezone": "UTC"})
    assert utc_summary.status_code == 200
    utc_pullups = next(item for item in utc_summary.json()["today"] if item["exercise_slug"] == "pullups")

    adt_summary = client.get("/api/dashboard/summary", headers={"X-Timezone": "America/Halifax"})
    assert adt_summary.status_code == 200
    adt_pullups = next(item for item in adt_summary.json()["today"] if item["exercise_slug"] == "pullups")
    assert sorted([utc_pullups["totals"]["reps"], adt_pullups["totals"]["reps"]]) == [0, 5]


def test_dashboard_summary_uses_3am_training_day_cutoff(client):
    before_cutoff_utc, after_cutoff_utc = around_training_cutoff_utc_timestamps("UTC")

    before = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})
    assert before.status_code == 200
    set_log_timestamp(before.json()["id"], before_cutoff_utc)

    after = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 7})
    assert after.status_code == 200
    set_log_timestamp(after.json()["id"], after_cutoff_utc)

    response = client.get("/api/dashboard/summary", headers={"X-Timezone": "UTC"})
    assert response.status_code == 200
    body = response.json()

    pullups_today = next(item for item in body["today"] if item["exercise_slug"] == "pullups")
    pullups_last_30 = next(item for item in body["last_30_days"] if item["exercise_slug"] == "pullups")
    assert pullups_today["totals"]["reps"] == 7
    assert pullups_last_30["totals"]["reps"] == 12
    assert body["total_logs_today"] == 1


def test_dashboard_summary_invalid_timezone_falls_back_to_utc(client):
    create_response = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})
    assert create_response.status_code == 200
    set_log_timestamp(create_response.json()["id"], cross_day_utc_timestamp("America/Halifax"))

    invalid_response = client.get("/api/dashboard/summary", headers={"X-Timezone": "Not/A_Real_Zone"})
    utc_response = client.get("/api/dashboard/summary", headers={"X-Timezone": "UTC"})

    assert invalid_response.status_code == 200
    assert utc_response.status_code == 200

    invalid_pullups = next(item for item in invalid_response.json()["today"] if item["exercise_slug"] == "pullups")
    utc_pullups = next(item for item in utc_response.json()["today"] if item["exercise_slug"] == "pullups")
    assert invalid_pullups["totals"]["reps"] == utc_pullups["totals"]["reps"]


def test_dashboard_summary_missing_timezone_defaults_to_utc(client):
    client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})

    no_header = client.get("/api/dashboard/summary")
    utc_header = client.get("/api/dashboard/summary", headers={"X-Timezone": "UTC"})

    assert no_header.status_code == 200
    assert utc_header.status_code == 200

    no_header_pullups = next(item for item in no_header.json()["today"] if item["exercise_slug"] == "pullups")
    utc_pullups = next(item for item in utc_header.json()["today"] if item["exercise_slug"] == "pullups")
    assert no_header_pullups["totals"]["reps"] == utc_pullups["totals"]["reps"]


def test_dashboard_summary_consistency_rows_have_30_days(client):
    client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})

    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    pullups = next(item for item in body["last_30_days_consistency"] if item["exercise_slug"] == "pullups")
    assert len(pullups["days"]) == 30
    assert pullups["active_days"] >= 1


def test_dashboard_summary_goal_scaled_intensity_uses_medium_range(client):
    client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 36})

    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    pullups = next(item for item in body["last_30_days_consistency"] if item["exercise_slug"] == "pullups")
    today = pullups["days"][-1]

    assert pullups["scaling_mode"] == "goal"
    assert pullups["goal_target_value"] == 40
    assert today["progress_value"] == 36
    assert today["intensity_level"] == 2


def test_dashboard_summary_goal_scaled_intensity_supports_high_and_peak(client):
    client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 60})

    high_response = client.get("/api/dashboard/summary")
    assert high_response.status_code == 200
    high_pullups = next(
        item for item in high_response.json()["last_30_days_consistency"] if item["exercise_slug"] == "pullups"
    )
    assert high_pullups["days"][-1]["intensity_level"] == 3

    client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 20})

    peak_response = client.get("/api/dashboard/summary")
    assert peak_response.status_code == 200
    peak_pullups = next(
        item for item in peak_response.json()["last_30_days_consistency"] if item["exercise_slug"] == "pullups"
    )
    assert peak_pullups["days"][-1]["progress_value"] == 80
    assert peak_pullups["days"][-1]["intensity_level"] == 4


def test_deleted_exercise_hidden_from_dashboard_and_recent(client):
    client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})
    exercises = client.get("/api/exercises").json()
    pullups = next(item for item in exercises if item["slug"] == "pullups")
    delete_response = client.delete(f"/api/exercises/{pullups['id']}")
    assert delete_response.status_code == 204

    summary = client.get("/api/dashboard/summary")
    assert summary.status_code == 200
    assert all(item["exercise_slug"] != "pullups" for item in summary.json()["today"])

    recent = client.get("/api/logs/recent?limit=20")
    assert recent.status_code == 200
    assert all(item["exercise_slug"] != "pullups" for item in recent.json())
