from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.log import CreateLogRequest, LogResponse, RecentLogItem
from app.services.log_service import create_log, get_recent_logs, hard_delete_log

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("", response_model=LogResponse)
def create_log_entry(payload: CreateLogRequest, db: Session = Depends(get_db)) -> LogResponse:
    return create_log(db, payload)


@router.get("/recent", response_model=list[RecentLogItem])
def recent_logs(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)) -> list[RecentLogItem]:
    return get_recent_logs(db, limit)


@router.delete("/{log_id}", status_code=204)
def delete_log_entry(log_id: int, db: Session = Depends(get_db)) -> None:
    hard_delete_log(db, log_id)
