from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cloud_attendance.models import Base, TimestampMixin, utcnow
from cloud_attendance.models.synced_verification_attempt import SyncedAttendanceType


class SyncedAttendanceEvent(Base, TimestampMixin):
    __tablename__ = "synced_attendance_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("synced_employees.id"), nullable=False)
    type: Mapped[SyncedAttendanceType] = mapped_column(Enum(SyncedAttendanceType, native_enum=False), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verification_attempt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("synced_verification_attempts.id"), nullable=False, unique=True
    )
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    employee: Mapped["SyncedEmployee"] = relationship(back_populates="attendance_events")  # noqa: F821
    verification_attempt: Mapped["SyncedVerificationAttempt"] = relationship(  # noqa: F821
        foreign_keys=[verification_attempt_id]
    )
