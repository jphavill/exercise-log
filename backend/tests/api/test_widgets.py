from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.exercise import Exercise

from .helpers import set_log_timestamp


def test_pullups_widget_returns_last_30_days_in_order(client):
    response = client.get("/api/widgets/pullups", headers={"X-Timezone": "UTC"})
    assert response.status_code == 200

    body = response.json()
    assert body["year_total"] == 0
    assert body["daily_goal"] == 40
    assert len(body["last_30_days"]) == 30

    today = datetime.now(UTC).date()
    assert body["last_30_days"][0]["date"] == (today - timedelta(days=29)).isoformat()
    assert body["last_30_days"][-1]["date"] == today.isoformat()
    assert all(day["count"] == 0 for day in body["last_30_days"])
    assert all(day["heat_level"] == 0 for day in body["last_30_days"])


def test_pullups_widget_aggregates_daily_totals_and_goal_heat(client):
    first = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 5})
    second = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 7})
    assert first.status_code == 200
    assert second.status_code == 200

    response = client.get("/api/widgets/pullups", headers={"X-Timezone": "UTC"})
    assert response.status_code == 200

    body = response.json()
    today = body["last_30_days"][-1]
    assert today["count"] == 12
    assert today["heat_level"] == 1
    assert body["year_total"] == 12


def test_pullups_widget_uses_relative_heat_when_goal_missing(client):
    with SessionLocal() as db:
        pullups = db.scalar(select(Exercise).where(Exercise.slug == "pullups"))
        assert pullups is not None
        pullups.goal_reps = None
        db.commit()

    first = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 8})
    second = client.post("/api/logs", json={"exercise_slug": "pullups", "reps": 4})
    assert first.status_code == 200
    assert second.status_code == 200

    second_id = second.json()["id"]
    yesterday = datetime.now(UTC).date() - timedelta(days=1)
    set_log_timestamp(second_id, datetime(yesterday.year, yesterday.month, yesterday.day, 10, 0, tzinfo=UTC))

    response = client.get("/api/widgets/pullups", headers={"X-Timezone": "UTC"})
    assert response.status_code == 200

    body = response.json()
    assert body["daily_goal"] is None

    yesterday_item = body["last_30_days"][-2]
    today_item = body["last_30_days"][-1]
    assert yesterday_item["count"] == 4
    assert yesterday_item["heat_level"] == 3
    assert today_item["count"] == 8
    assert today_item["heat_level"] == 4
