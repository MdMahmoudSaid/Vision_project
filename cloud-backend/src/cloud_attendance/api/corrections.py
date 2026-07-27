import json
from typing import Any, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from cloud_attendance.auth.dependencies import require_admin_or_owner
from cloud_attendance.database import get_db
from cloud_attendance.models.cloud_user import CloudUser
from cloud_attendance.schemas.correction import Correction, CorrectionCreate
from cloud_attendance.services.correction_service import create_correction, get_corrections_by_employee

router = APIRouter(prefix="/attendance/corrections", tags=["corrections"])


def format_correction(c) -> Correction:
    return Correction(
        id=c.id,
        employee_id=c.employee_id,
        attendance_event_id=c.attendance_event_id,
        action=c.action,
        previous_value=json.loads(c.previous_value) if c.previous_value else None,
        new_value=json.loads(c.new_value),
        reason=c.reason,
        performed_by=c.performed_by,
        performed_at=c.performed_at
    )


@router.post("", response_model=Correction, status_code=status.HTTP_201_CREATED)
def post_correction(
    payload: CorrectionCreate,
    db: Session = Depends(get_db),
    current_user: CloudUser = Depends(require_admin_or_owner)
) -> Correction:
    c = create_correction(db, payload, current_user.id)
    return format_correction(c)


@router.get("/{employee_id}", response_model=List[Correction])
def get_corrections(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: CloudUser = Depends(require_admin_or_owner)
) -> List[Correction]:
    corrections = get_corrections_by_employee(db, employee_id)
    return [format_correction(c) for c in corrections]
