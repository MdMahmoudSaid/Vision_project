import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


from cloud_attendance.models.cloud_user import CloudRole, CloudUser
from cloud_attendance.models.synced_employee import SyncedEmployee
from cloud_attendance.models.synced_verification_attempt import SyncedVerificationAttempt, SyncedAttendanceType, SyncedVerificationResult
from cloud_attendance.models.synced_attendance_event import SyncedAttendanceEvent
from cloud_attendance.models.sync_ingest_log import SyncIngestLog
from cloud_attendance.models.correction import Correction, CorrectionAction

__all__ = [
    "Base",
    "TimestampMixin",
    "generate_uuid",
    "utcnow",
    "CloudUser",
    "CloudRole",
    "SyncedEmployee",
    "SyncedVerificationAttempt",
    "SyncedAttendanceType",
    "SyncedVerificationResult",
    "SyncedAttendanceEvent",
    "SyncIngestLog",
    "Correction",
    "CorrectionAction",
]
