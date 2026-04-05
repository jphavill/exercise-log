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
