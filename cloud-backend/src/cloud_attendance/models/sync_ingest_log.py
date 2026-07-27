from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from cloud_attendance.models import Base, generate_uuid, utcnow


class SyncIngestLog(Base):
    __tablename__ = "sync_ingest_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    employees_accepted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verification_attempts_accepted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attendance_events_accepted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
