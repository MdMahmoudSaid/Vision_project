from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from local_attendance.models import Base, TimestampMixin, generate_uuid


def today() -> date:
    return datetime.now(timezone.utc).date()


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    registration_date: Mapped[date] = mapped_column(Date, nullable=False, default=today)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    facial_references: Mapped[list["FacialReference"]] = relationship(  # noqa: F821
        back_populates="employee", cascade="all, delete-orphan"
    )
    verification_attempts: Mapped[list["VerificationAttempt"]] = relationship(  # noqa: F821
        back_populates="employee"
    )
    attendance_events: Mapped[list["AttendanceEvent"]] = relationship(back_populates="employee")  # noqa: F821
