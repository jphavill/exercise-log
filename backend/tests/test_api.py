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


def test_dashboard_summary_output(client):
    client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})
    client.post("/api/logs", json={"exercise_slug": "l-sit", "duration_seconds": 15})

    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert "today" in body
    assert "current_week" in body
    assert body["total_logs_today"] >= 2


def test_history_endpoint_output(client):
    client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 4})
    response = client.get("/api/exercises/pullups/history?days=30")
    assert response.status_code == 200
    body = response.json()
    assert body["exercise"]["slug"] == "pullups"
    assert len(body["days"]) == 30
    assert "current_streak" in body


def test_create_exercise_endpoint(client):
    response = client.post(
        "/api/exercises",
        json={
            "slug": "dead-hang",
            "name": "Dead Hang",
            "metric_type": "duration_seconds",
            "sort_order": 5,
        },
    )
    assert response.status_code == 201
    assert response.json()["slug"] == "dead-hang"


def test_update_exercise_endpoint(client):
    exercises = client.get("/api/exercises").json()
    target = exercises[0]

    response = client.put(
        f"/api/exercises/{target['id']}",
        json={"name": "Updated Name", "metric_type": target["metric_type"], "sort_order": 9},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Updated Name"
    assert body["sort_order"] == 9


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


def test_delete_exercise_soft_delete_hides_from_list(client):
    exercises = client.get("/api/exercises").json()
    target = exercises[0]

    response = client.delete(f"/api/exercises/{target['id']}")
    assert response.status_code == 204

    remaining = client.get("/api/exercises").json()
    remaining_ids = {item["id"] for item in remaining}
    assert target["id"] not in remaining_ids


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
