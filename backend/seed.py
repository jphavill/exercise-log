from app.db.seed import seed_exercises
from app.db.session import SessionLocal


def run() -> None:
    with SessionLocal() as db:
        seed_exercises(db)


if __name__ == "__main__":
    run()
