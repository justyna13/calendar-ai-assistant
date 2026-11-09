from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from services.google_calendar import list_events
from services.session_store import get_account_for_session

router = APIRouter(prefix="/calendar", tags=["calendar"])

@router.get("/events")
def get_calendar_events(
    time_min: datetime,
    time_max: datetime,
    request: Request,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if time_min.tzinfo is None or time_max.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="time_min and time_max must include a timezone"
        )

    if time_min >= time_max:
        raise HTTPException(
            status_code=400,
            detail="time_min must be earlier than time_max",
        )

    account = get_account_for_session(
        request.cookies.get("session"),
        db
    )
    if account is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return list_events(account, time_min, time_max)