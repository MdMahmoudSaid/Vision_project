import json
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from local_attendance.camera.base import CameraBase, CameraCaptureError
from local_attendance.face.engine import FaceEngineBase
from local_attendance.models import utcnow
from local_attendance.models.employee import Employee
from local_attendance.models.facial_reference import FacialReference, FacialReferenceQuality
from local_attendance.models.user import LocalUser


class FaceEnrollmentUnusableError(Exception):
    """Raised when the camera itself could not produce frames at all."""

    pass


class FaceEnrollmentNoFaceError(Exception):
    """Raised when the camera worked, but a clear face could not be captured
    in any of the retries — the employee should adjust their position/posture
    and the admin should retry."""

    pass


# Each capture the camera actually produces is retried against the face
# engine independently; a failed sample (blurry, no face, employee not yet in
# frame) just costs one extra capture rather than failing the whole
# enrollment. This bounds how many extra attempts we'll make before giving up
# and asking the admin to retry — generous enough to ride out a few bad
# frames, bounded so a persistently empty camera doesn't hang the request.
_MAX_ATTEMPTS_PER_SAMPLE = 5

# A single capture+detect attempt normally takes ~1-3 seconds (camera
# warm-up plus CPU face detection/embedding). The attempt-count cap above
# does not, by itself, bound wall-clock time — on a slower machine or under
# camera contention it could still take the better part of a minute with no
# feedback to the admin. This wall-clock deadline is the real bound: once
# reached, we stop retrying and fail with a clear "no face" error, even if
# the attempt-count budget hasn't been exhausted yet.
_MAX_TOTAL_SECONDS = 12.0


def enroll_face(
    db: Session,
    employee: Employee,
    admin: LocalUser,
    camera: CameraBase,
    face_engine: FaceEngineBase,
    sample_count: int = 3,
) -> FacialReference:
    embeddings: list[list[float]] = []
    max_attempts = sample_count * _MAX_ATTEMPTS_PER_SAMPLE
    attempts = 0
    deadline = time.monotonic() + _MAX_TOTAL_SECONDS

    while len(embeddings) < sample_count and attempts < max_attempts and time.monotonic() < deadline:
        attempts += 1
        try:
            frame = camera.capture_frame()
        except CameraCaptureError as exc:
            raise FaceEnrollmentUnusableError("Camera could not capture a usable frame") from exc

        embedding = face_engine.enroll_sample(frame)
        if embedding is not None:
            embeddings.append(embedding)

    if len(embeddings) < sample_count:
        raise FaceEnrollmentNoFaceError(
            "Could not get a clear view of the employee's face. "
            "Ask them to face the camera directly with good lighting and try again."
        )

    averaged = _average_embeddings(embeddings)

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
        embedding=json.dumps(averaged),
        sample_count=len(embeddings),
        quality_status=FacialReferenceQuality.USABLE,
        created_by_user_id=admin.id,
    )
    db.add(reference)
    db.commit()
    db.refresh(reference)
    return reference


def _average_embeddings(embeddings: list[list[float]]) -> list[float]:
    dimensions = len(embeddings[0])
    return [sum(embedding[i] for embedding in embeddings) / len(embeddings) for i in range(dimensions)]
