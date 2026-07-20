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


from local_attendance.models.employee import Employee  # noqa: E402
from local_attendance.models.user import LocalUser  # noqa: E402
from local_attendance.models.facial_reference import FacialReference  # noqa: E402
from local_attendance.models.verification_attempt import VerificationAttempt  # noqa: E402
from local_attendance.models.attendance_event import AttendanceEvent  # noqa: E402
from local_attendance.models.setting import LocalSetting  # noqa: E402

__all__ = [
    "Base",
    "TimestampMixin",
    "utcnow",
    "generate_uuid",
    "Employee",
    "LocalUser",
    "FacialReference",
    "VerificationAttempt",
    "AttendanceEvent",
    "LocalSetting",
]
