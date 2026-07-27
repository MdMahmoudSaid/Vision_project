from datetime import datetime
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cloud_attendance.models import Base, TimestampMixin, utcnow


class SyncedEmployee(Base, TimestampMixin):
    __tablename__ = "synced_employees"

    # ID is reused verbatim from the local Employee.id
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_number: Mapped[str] = mapped_column(String(64), nullable=False)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    has_face_reference: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    verification_attempts: Mapped[list["SyncedVerificationAttempt"]] = relationship(back_populates="employee")  # noqa: F821
    attendance_events: Mapped[list["SyncedAttendanceEvent"]] = relationship(back_populates="employee")  # noqa: F821
