import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cloud_attendance.models import Base, generate_uuid, utcnow


class CorrectionAction(str, enum.Enum):
    ADD_ARRIVAL = "add_arrival"
    ADD_DEPARTURE = "add_departure"
    CORRECT_TIME = "correct_time"
    CHANGE_TYPE = "change_type"


class Correction(Base):
    __tablename__ = "corrections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("synced_employees.id"), nullable=False)
    attendance_event_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("synced_attendance_events.id"), nullable=True)
    action: Mapped[CorrectionAction] = mapped_column(Enum(CorrectionAction, native_enum=False), nullable=False)
    previous_value: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON text
    new_value: Mapped[str] = mapped_column(Text, nullable=False)  # JSON text
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    performed_by: Mapped[str] = mapped_column(String(36), ForeignKey("cloud_users.id"), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    employee: Mapped["SyncedEmployee"] = relationship(foreign_keys=[employee_id])  # noqa: F821
    attendance_event: Mapped["SyncedAttendanceEvent"] = relationship(foreign_keys=[attendance_event_id])  # noqa: F821
    user: Mapped["CloudUser"] = relationship(foreign_keys=[performed_by])  # noqa: F821
