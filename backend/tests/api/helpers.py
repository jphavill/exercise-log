from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from app.db.session import SessionLocal
from app.models.exercise_log import ExerciseLog


def set_log_timestamp(log_id: int, value: datetime) -> None:
    with SessionLocal() as db:
        log = db.get(ExerciseLog, log_id)
        assert log is not None
        log.logged_at = value
        db.commit()


def cross_day_utc_timestamp(timezone_name: str) -> datetime:
    timezone = ZoneInfo(timezone_name)
    now_utc = datetime.now(UTC)
    utc_today = now_utc.date()
    local_today = now_utc.astimezone(timezone).date()

    candidate_times = [time(21, 0), time(0, 30)]
    for candidate_time in candidate_times:
        candidate_local = datetime.combine(local_today, candidate_time, tzinfo=timezone)
        candidate_utc = candidate_local.astimezone(UTC)
        if candidate_utc.date() != utc_today:
            return candidate_utc

    raise AssertionError("Could not create a cross-day timestamp for timezone test")
