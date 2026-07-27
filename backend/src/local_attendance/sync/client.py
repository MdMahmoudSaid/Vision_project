import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from local_attendance.config import get_settings
from local_attendance.models.attendance_event import AttendanceEvent
from local_attendance.models.employee import Employee
from local_attendance.models.facial_reference import FacialReference, FacialReferenceQuality
from local_attendance.models.verification_attempt import VerificationAttempt

logger = logging.getLogger(__name__)


def _has_usable_face_reference(db: Session, employee_id: str) -> bool:
    """Same USABLE-and-not-replaced definition used by the local API's own
    employee listing (local_attendance/api/employees.py) — a raw count of
    facial_references rows would incorrectly report True for an employee
    whose only reference was rejected or has since been replaced."""
    return (
        db.scalar(
            select(FacialReference.id).where(
                FacialReference.employee_id == employee_id,
                FacialReference.quality_status == FacialReferenceQuality.USABLE,
                FacialReference.replaced_at.is_(None),
            )
        )
        is not None
    )


async def run_sync_batch(db: Session) -> bool:
    """Returns True on a successful push (or when there was nothing to
    push), False on a failure, so the scheduler can back off on repeated
    failures instead of retrying at a fixed interval regardless of outcome."""
    settings = get_settings()
    if not settings.sync_target_url or not settings.sync_api_key:
        logger.warning("Sync target URL or API key not configured. Skipping sync.")
        return True

    # Gather unsynced records
    # Limit batch size to prevent massive payloads if offline for a long time
    BATCH_SIZE = 50

    unsynced_employees = db.scalars(
        select(Employee).where(Employee.synced == False).limit(BATCH_SIZE)  # noqa: E712
    ).all()
    
    unsynced_attempts = db.scalars(
        select(VerificationAttempt).where(VerificationAttempt.synced == False).limit(BATCH_SIZE)  # noqa: E712
    ).all()
    
    unsynced_events = db.scalars(
        select(AttendanceEvent).where(AttendanceEvent.synced == False).limit(BATCH_SIZE)  # noqa: E712
    ).all()

    if not unsynced_employees and not unsynced_attempts and not unsynced_events:
        return True

    # synced_at is stamped by the cloud itself at ingestion time (it means
    # "when the cloud last received an update for this employee"), so what we
    # send here is just a placeholder the cloud overwrites — never trust a
    # client-reported receipt time as the cloud's own bookkeeping field.
    now = datetime.now(timezone.utc).isoformat()
    payload: dict[str, Any] = {
        "employees": [
            {
                "id": e.id,
                "full_name": e.full_name,
                "employee_number": e.employee_number,
                "department": e.department,
                "active": e.active,
                "has_face_reference": _has_usable_face_reference(db, e.id),
                "synced_at": now,
            }
            for e in unsynced_employees
        ],
        "verification_attempts": [
            {
                "id": a.id,
                "employee_id": a.employee_id,
                "type_requested": a.type_requested.value,
                "timestamp": a.timestamp.isoformat(),
                "result": a.result.value,
                "similarity_score": a.similarity_score,
                "failure_reason": a.failure_reason,
                "attendance_event_id": a.attendance_event_id,
            }
            for a in unsynced_attempts
        ],
        "attendance_events": [
            {
                "id": e.id,
                "employee_id": e.employee_id,
                "type": e.type.value,
                "timestamp": e.timestamp.isoformat(),
                "verification_attempt_id": e.verification_attempt_id,
            }
            for e in unsynced_events
        ],
    }

    url = f"{settings.sync_target_url.rstrip('/')}/sync/batch"
    headers = {"X-Sync-Api-Key": settings.sync_api_key}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            if response.status_code == 200:
                # Mark as synced
                for e in unsynced_employees:
                    e.synced = True
                for a in unsynced_attempts:
                    a.synced = True
                for evt in unsynced_events:
                    evt.synced = True
                db.commit()
                logger.info("Successfully synced %d employees, %d attempts, %d events", len(unsynced_employees), len(unsynced_attempts), len(unsynced_events))
                return True
            logger.error("Sync failed with status %d: %s", response.status_code, response.text)
            return False
    except httpx.RequestError as exc:
        logger.error("Sync request failed: %s", exc)
        return False
