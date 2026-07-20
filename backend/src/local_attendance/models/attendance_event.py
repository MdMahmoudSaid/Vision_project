import enum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from local_attendance.models import Base, TimestampMixin, generate_uuid, utcnow
from local_attendance.models.verification_attempt import AttendanceType


class AttendanceSource(str, enum.Enum):
    AUTO = "auto"


class AttendanceEvent(Base, TimestampMixin):
    __tablename__ = "attendance_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False)
    type: Mapped[AttendanceType] = mapped_column(Enum(AttendanceType, native_enum=False), nullable=False)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    guard_id: Mapped[str] = mapped_column(String(36), ForeignKey("local_users.id"), nullable=False)
    verification_attempt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("verification_attempts.id"), nullable=False, unique=True
    )
    source: Mapped[AttendanceSource] = mapped_column(
        Enum(AttendanceSource, native_enum=False), nullable=False, default=AttendanceSource.AUTO
    )
    synced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    employee: Mapped["Employee"] = relationship(back_populates="attendance_events")  # noqa: F821
    guard: Mapped["LocalUser"] = relationship(foreign_keys=[guard_id])  # noqa: F821
    verification_attempt: Mapped["VerificationAttempt"] = relationship(  # noqa: F821
        foreign_keys=[verification_attempt_id]
    )
