import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError


def _resolve_test_db_path() -> Path:
    tests_dir = Path(__file__).resolve().parent
    worker_id = os.getenv("PYTEST_XDIST_WORKER")
    db_name = "exercise_test"
    if worker_id:
        db_name = f"exercise_{worker_id}_test"

    db_path = tests_dir / f"{db_name}.sqlite3"
    if not db_path.stem.endswith("_test"):
        raise RuntimeError(f"Refusing to use non-test database path: {db_path}")

    return db_path


TEST_DB_PATH = _resolve_test_db_path()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["AUTO_SEED"] = "false"

from app.db.base import Base
from app.db.seed import seed_exercises
from app.db.session import SessionLocal, engine
from app.main import app


def _clear_all_tables() -> None:
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
        try:
            connection.exec_driver_sql("DELETE FROM sqlite_sequence")
        except OperationalError:
            pass


@pytest.fixture(scope="session", autouse=True)
def initialize_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)
    TEST_DB_PATH.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def isolate_database() -> None:
    _clear_all_tables()
    with SessionLocal() as db:
        seed_exercises(db)


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
