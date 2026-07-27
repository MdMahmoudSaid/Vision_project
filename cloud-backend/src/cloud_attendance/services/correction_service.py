import json
from datetime import timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from cloud_attendance.models import Correction, CorrectionAction, SyncedAttendanceEvent, SyncedEmployee
from cloud_attendance.schemas.correction import CorrectionCreate


def create_correction(
    db: Session,
    payload: CorrectionCreate,
    performed_by: str
) -> Correction:
    # 1. Enforce reason non-empty
    if not payload.reason.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_reason", "message": "Reason must not be empty"}
        )

    # 2. Check employee exists
    employee = db.get(SyncedEmployee, payload.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Employee not found"}
        )

    previous_value = None

    # 3. Validate based on action
    if payload.action in (CorrectionAction.ADD_ARRIVAL, CorrectionAction.ADD_DEPARTURE):
        if payload.attendance_event_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_correction", "message": f"{payload.action.value} must not reference an existing attendance_event_id"}
            )
        # Verify that new_value contains the timestamp
        if "timestamp" not in payload.new_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_value", "message": "new_value must contain timestamp"}
            )
    else: # CORRECT_TIME, CHANGE_TYPE
        if payload.attendance_event_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_correction", "message": f"{payload.action.value} must reference an existing attendance_event_id"}
            )
        
        event = db.get(SyncedAttendanceEvent, payload.attendance_event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "not_found", "message": "Attendance event not found"}
            )

        if payload.action == CorrectionAction.CORRECT_TIME:
            if "timestamp" not in payload.new_value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "invalid_value", "message": "new_value must contain timestamp"}
                )
            # SQLite does not reliably round-trip tzinfo even on a
            # DateTime(timezone=True) column, so a naive value read back
            # would otherwise produce an ambiguous ISO string with no
            # offset — always normalize to UTC-aware before serializing.
            stored_ts = event.timestamp
            if stored_ts.tzinfo is None:
                stored_ts = stored_ts.replace(tzinfo=timezone.utc)
            previous_value = {"timestamp": stored_ts.isoformat()}
        else: # CHANGE_TYPE
            if "type" not in payload.new_value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "invalid_value", "message": "new_value must contain type"}
                )
            previous_value = {"type": event.type}

    correction = Correction(
        employee_id=payload.employee_id,
        attendance_event_id=payload.attendance_event_id,
        action=payload.action,
        previous_value=json.dumps(previous_value) if previous_value else None,
        new_value=json.dumps(payload.new_value),
        reason=payload.reason,
        performed_by=performed_by
    )
    
    db.add(correction)
    db.commit()
    db.refresh(correction)
    return correction


def get_corrections_by_employee(db: Session, employee_id: str) -> List[Correction]:
    return db.scalars(
        select(Correction)
        .where(Correction.employee_id == employee_id)
        .order_by(Correction.performed_at.asc())
    ).all()
