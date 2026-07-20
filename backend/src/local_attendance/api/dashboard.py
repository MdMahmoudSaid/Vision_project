from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from local_attendance.auth.dependencies import require_guard_or_admin
from local_attendance.database import get_db
from local_attendance.models.user import LocalUser
from local_attendance.schemas.dashboard import LocalOverview
from local_attendance.services.attendance_service import get_local_overview

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=LocalOverview)
def overview(
    db: Session = Depends(get_db),
    _: LocalUser = Depends(require_guard_or_admin),
) -> LocalOverview:
    today = datetime.now(timezone.utc).date()
    record = get_local_overview(db, today)
    return LocalOverview(
        date=record.date,
        arrivals=record.arrivals,
        departures=record.departures,
        failed_attempts=record.failed_attempts,
    )
