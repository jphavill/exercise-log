from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from app.api.dependencies import request_timezone
from app.db.session import get_db
from app.schemas.widget import PullupsWidgetResponse
from app.services.widgets import get_pullups_widget

router = APIRouter(prefix="/widgets", tags=["widgets"])


@router.get("/pullups", response_model=PullupsWidgetResponse)
def pullups_widget(
    db: Session = Depends(get_db),
    timezone: ZoneInfo = Depends(request_timezone),
) -> PullupsWidgetResponse:
    return get_pullups_widget(db, timezone)
