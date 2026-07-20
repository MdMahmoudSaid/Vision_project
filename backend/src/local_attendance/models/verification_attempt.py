import enum

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from local_attendance.models import Base, TimestampMixin, generate_uuid, utcnow


class AttendanceType(str, enum.Enum):
    ARRIVAL = "arrival"
    DEPARTURE = "departure"


class VerificationResult(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    DUPLICATE_BLOCKED = "duplicate_blocked"


class VerificationAttempt(Base, TimestampMixin):
    __tablename__ = "verification_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False)
    guard_id: Mapped[str] = mapped_column(String(36), ForeignKey("local_users.id"), nullable=False)
    type_requested: Mapped[AttendanceType] = mapped_column(Enum(AttendanceType, native_enum=False), nullable=False)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    result: Mapped[VerificationResult] = mapped_column(Enum(VerificationResult, native_enum=False), nullable=False)
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Denormalized pointer set after a linked AttendanceEvent is created. Not a DB-level
    # foreign key: attendance_events.verification_attempt_id is the authoritative FK, and a
    # mutual FK here would create an unresolvable table-creation cycle for migrations.
    attendance_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    synced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    employee: Mapped["Employee"] = relationship(back_populates="verification_attempts")  # noqa: F821
    guard: Mapped["LocalUser"] = relationship(foreign_keys=[guard_id])  # noqa: F821
