from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from app.api.dependencies import request_timezone
from app.db.session import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard import get_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    db: Session = Depends(get_db),
    timezone: ZoneInfo = Depends(request_timezone),
) -> DashboardSummaryResponse:
    return get_summary(db, timezone)
