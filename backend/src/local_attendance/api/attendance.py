from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from local_attendance.auth.dependencies import require_guard_or_admin
from local_attendance.camera.base import CameraBase, get_camera
from local_attendance.database import get_db
from local_attendance.face.engine import FaceEngineBase, get_face_engine
from local_attendance.models.user import LocalUser
from local_attendance.schemas.attendance import AttendanceEvent as AttendanceEventSchema
from local_attendance.schemas.attendance import AttendanceVerifyRequest, AttendanceVerifyResponse
from local_attendance.schemas.attendance import VerificationAttempt as VerificationAttemptSchema
from local_attendance.schemas.dashboard import ShiftActivityItem
from local_attendance.services.attendance_service import get_shift_activity
from local_attendance.services.verification_service import BAD_REQUEST_STATUSES, verify_attendance

router = APIRouter(prefix="/attendance", tags=["attendance"])

_BAD_REQUEST_MESSAGES = {
    "employee_not_found": "Employee not found",
    "employee_inactive": "Employee is not active",
    "missing_reference": "Employee has no usable facial reference",
    "capture_unusable": "Camera could not capture a usable frame",
    "face_not_detected": "No usable face detected in the capture",
}


@router.post("/verify", response_model=AttendanceVerifyResponse)
def verify(
    payload: AttendanceVerifyRequest,
    db: Session = Depends(get_db),
    guard: LocalUser = Depends(require_guard_or_admin),
    camera: CameraBase = Depends(get_camera),
    face_engine: FaceEngineBase = Depends(get_face_engine),
) -> AttendanceVerifyResponse:
    outcome = verify_attendance(
        db=db,
        employee_id=payload.employee_id,
        type_requested=payload.type,
        guard=guard,
        camera=camera,
        face_engine=face_engine,
    )

    if outcome.status in BAD_REQUEST_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": outcome.status, "message": _BAD_REQUEST_MESSAGES[outcome.status]},
        )

    return AttendanceVerifyResponse(
        result=outcome.attempt.result,
        message=outcome.message,
        verification_attempt=VerificationAttemptSchema.model_validate(outcome.attempt),
        attendance_event=(
            AttendanceEventSchema.model_validate(outcome.attendance_event) if outcome.attendance_event else None
        ),
    )


@router.get("/shift-activity", response_model=list[ShiftActivityItem])
def shift_activity(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: LocalUser = Depends(require_guard_or_admin),
) -> list[ShiftActivityItem]:
    records = get_shift_activity(db, limit=limit)
    return [
        ShiftActivityItem(
            kind=record.kind,
            employee_id=record.employee_id,
            employee_name=record.employee_name,
            type=record.type,
            timestamp=record.timestamp,
            guard_username=record.guard_username,
            outcome=record.outcome,
            failure_reason=record.failure_reason,
            attendance_event_id=record.attendance_event_id,
        )
        for record in records
    ]
