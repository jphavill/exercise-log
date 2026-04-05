from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.exercises import router as exercises_router
from app.api.routes.logs import router as logs_router
from app.api.routes.widgets import router as widgets_router
from app.core.config import settings
from app.db.seed import seed_exercises
from app.db.session import SessionLocal


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_seed:
        with SessionLocal() as db:
            seed_exercises(db)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(logs_router, prefix="/api")
app.include_router(exercises_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(widgets_router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
