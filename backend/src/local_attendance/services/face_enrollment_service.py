import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from local_attendance.camera.base import CameraBase, CameraCaptureError
from local_attendance.face.engine import FaceEngineBase
from local_attendance.models import utcnow
from local_attendance.models.employee import Employee
from local_attendance.models.facial_reference import FacialReference, FacialReferenceQuality
from local_attendance.models.user import LocalUser


class FaceEnrollmentUnusableError(Exception):
    pass


def enroll_face(
    db: Session,
    employee: Employee,
    admin: LocalUser,
    camera: CameraBase,
    face_engine: FaceEngineBase,
    sample_count: int = 3,
) -> FacialReference:
    samples = []
    for _ in range(sample_count):
        try:
            samples.append(camera.capture_frame())
        except CameraCaptureError as exc:
            raise FaceEnrollmentUnusableError("Camera could not capture a usable frame") from exc

    result = face_engine.enroll(samples)
    if not result.usable or not result.embedding:
        raise FaceEnrollmentUnusableError("No usable face could be produced from the capture")

    existing = db.scalar(
        select(FacialReference).where(
            FacialReference.employee_id == employee.id,
            FacialReference.quality_status == FacialReferenceQuality.USABLE,
            FacialReference.replaced_at.is_(None),
        )
    )
    if existing is not None:
        existing.replaced_at = utcnow()

    reference = FacialReference(
        employee_id=employee.id,
        embedding=json.dumps(result.embedding),
        sample_count=result.sample_count,
        quality_status=FacialReferenceQuality.USABLE,
        created_by_user_id=admin.id,
    )
    db.add(reference)
    db.commit()
    db.refresh(reference)
    return reference
