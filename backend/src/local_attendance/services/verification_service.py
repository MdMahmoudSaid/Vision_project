import json
import threading
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from local_attendance.camera.base import CameraBase, CameraCaptureError
from local_attendance.face.engine import FaceEngineBase, FaceEngineError
from local_attendance.models.attendance_event import AttendanceEvent
from local_attendance.models.employee import Employee
from local_attendance.models.facial_reference import FacialReference, FacialReferenceQuality
from local_attendance.models import utcnow
from local_attendance.models.user import LocalUser
from local_attendance.models.verification_attempt import AttendanceType, VerificationAttempt, VerificationResult
from local_attendance.services.attendance_service import create_attendance_event, find_recent_duplicate_event
from local_attendance.services.settings_service import get_duplicate_window_seconds

# Outcome statuses that are not surfaced as a 200 AttendanceVerifyResponse; the API layer
# maps these to a 400 ErrorResponse per contracts/local-api.yaml.
BAD_REQUEST_STATUSES = {
    "employee_not_found",
    "employee_inactive",
    "missing_reference",
    "capture_unusable",
    "face_not_detected",
    "spoof_detected",
}


@dataclass
class VerificationOutcome:
    status: str
    attempt: VerificationAttempt | None
    attendance_event: AttendanceEvent | None
    message: str


# FastAPI runs sync path operations in a thread pool, so two concurrent
# POST /attendance/verify calls for the same employee/type (double-tap, client
# retry) could both read "no recent duplicate" before either commits, creating
# two attendance events. This local-PC service is a single process, so a
# simple in-process lock around the check-then-write section is sufficient to
# make it atomic without needing SQLite-level locking gymnastics.
_duplicate_check_lock = threading.Lock()


def _latest_usable_reference(db: Session, employee_id: str) -> FacialReference | None:
    return db.scalar(
        select(FacialReference)
        .where(
            FacialReference.employee_id == employee_id,
            FacialReference.quality_status == FacialReferenceQuality.USABLE,
            FacialReference.replaced_at.is_(None),
        )
        .order_by(FacialReference.created_at.desc())
    )


def _record_attempt(
    db: Session,
    employee: Employee,
    guard: LocalUser,
    type_requested: AttendanceType,
    result: VerificationResult,
    similarity_score: float | None = None,
    failure_reason: str | None = None,
) -> VerificationAttempt:
    attempt = VerificationAttempt(
        employee_id=employee.id,
        guard_id=guard.id,
        type_requested=type_requested,
        result=result,
        similarity_score=similarity_score,
        failure_reason=failure_reason,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def verify_attendance(
    db: Session,
    employee_id: str,
    type_requested: AttendanceType,
    guard: LocalUser,
    camera: CameraBase,
    face_engine: FaceEngineBase,
) -> VerificationOutcome:
    employee = db.get(Employee, employee_id)
    if employee is None:
        return VerificationOutcome("employee_not_found", None, None, "Employee not found")

    if not employee.active:
        attempt = _record_attempt(
            db, employee, guard, type_requested, VerificationResult.FAILED, failure_reason="employee_inactive"
        )
        return VerificationOutcome("employee_inactive", attempt, None, "Employee is not active")

    reference = _latest_usable_reference(db, employee.id)
    if reference is None:
        attempt = _record_attempt(
            db, employee, guard, type_requested, VerificationResult.FAILED, failure_reason="missing_reference"
        )
        return VerificationOutcome("missing_reference", attempt, None, "Employee has no usable facial reference")

    try:
        frame = camera.capture_frame()
    except CameraCaptureError:
        attempt = _record_attempt(
            db, employee, guard, type_requested, VerificationResult.FAILED, failure_reason="capture_unusable"
        )
        return VerificationOutcome("capture_unusable", attempt, None, "Camera could not capture a usable frame")

    reference_embedding = json.loads(reference.embedding)

    try:
        comparison = face_engine.compare(frame, reference_embedding)
    except FaceEngineError as exc:
        reason = getattr(exc, "reason", "face_not_detected")
        attempt = _record_attempt(db, employee, guard, type_requested, VerificationResult.FAILED, failure_reason=reason)
        if reason == "spoof_detected":
            return VerificationOutcome(
                "spoof_detected", attempt, None, "Capture rejected: photo or screen detected instead of a live face"
            )
        return VerificationOutcome("face_not_detected", attempt, None, "No usable face detected in the capture")

    if not comparison.is_match:
        attempt = _record_attempt(
            db,
            employee,
            guard,
            type_requested,
            VerificationResult.FAILED,
            similarity_score=comparison.similarity_score,
            failure_reason="face_mismatch",
        )
        return VerificationOutcome("failed", attempt, None, "Face verification failed")

    with _duplicate_check_lock:
        now = utcnow()
        duplicate_window = get_duplicate_window_seconds(db)
        duplicate_event = find_recent_duplicate_event(db, employee.id, type_requested, duplicate_window, now)

        if duplicate_event is not None:
            attempt = _record_attempt(
                db,
                employee,
                guard,
                type_requested,
                VerificationResult.DUPLICATE_BLOCKED,
                similarity_score=comparison.similarity_score,
                failure_reason="duplicate_recent_attendance",
            )
            return VerificationOutcome(
                "duplicate_blocked", attempt, None, "Recent attendance was already recorded for this employee"
            )

        attempt = _record_attempt(
            db,
            employee,
            guard,
            type_requested,
            VerificationResult.SUCCESS,
            similarity_score=comparison.similarity_score,
        )

        event = create_attendance_event(db, employee=employee, guard=guard, type_=type_requested, attempt=attempt)

    return VerificationOutcome("success", attempt, event, "Attendance recorded")
