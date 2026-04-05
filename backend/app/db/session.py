from collections.abc import Generator
from datetime import UTC, datetime
from sqlite3 import Connection as SqliteConnection

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.timezone import ensure_utc, resolve_timezone


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _parse_sqlite_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return ensure_utc(value)

    if isinstance(value, bytes):
        text = value.decode("utf-8")
    else:
        text = str(value)

    candidate = text.strip()
    if candidate.endswith("Z"):
        candidate = f"{candidate[:-1]}+00:00"

    parsed = datetime.fromisoformat(candidate)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def _local_day_utc_iso(logged_at_value: object, timezone_name: str | None) -> str | None:
    if logged_at_value is None:
        return None

    timezone = resolve_timezone(timezone_name)
    logged_at_utc = _parse_sqlite_datetime(logged_at_value)
    return logged_at_utc.astimezone(timezone).date().isoformat()


if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _register_sqlite_functions(dbapi_connection: object, _: object) -> None:
        if isinstance(dbapi_connection, SqliteConnection):
            dbapi_connection.create_function("local_day_utc_iso", 2, _local_day_utc_iso)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
