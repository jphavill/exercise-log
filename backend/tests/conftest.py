import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = f"sqlite:///{Path(__file__).resolve().parent / 'test.sqlite3'}"
os.environ["AUTO_SEED"] = "false"

from app.db.base import Base
from app.db.seed import seed_exercises
from app.db.session import SessionLocal, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_exercises(db)

    with TestClient(app) as test_client:
        yield test_client
