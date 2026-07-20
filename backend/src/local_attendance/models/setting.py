from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from local_attendance.models import Base, utcnow


class LocalSetting(Base):
    __tablename__ = "local_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
