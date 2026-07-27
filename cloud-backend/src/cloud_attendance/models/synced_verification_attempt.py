import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cloud_attendance.models import Base, TimestampMixin, utcnow


class SyncedAttendanceType(str, enum.Enum):
    ARRIVAL = "arrival"
    DEPARTURE = "departure"


class SyncedVerificationResult(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    DUPLICATE_BLOCKED = "duplicate_blocked"


class SyncedVerificationAttempt(Base, TimestampMixin):
    __tablename__ = "synced_verification_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("synced_employees.id"), nullable=False)
    type_requested: Mapped[SyncedAttendanceType] = mapped_column(Enum(SyncedAttendanceType, native_enum=False), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    result: Mapped[SyncedVerificationResult] = mapped_column(Enum(SyncedVerificationResult, native_enum=False), nullable=False)
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attendance_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    employee: Mapped["SyncedEmployee"] = relationship(back_populates="verification_attempts")  # noqa: F821
