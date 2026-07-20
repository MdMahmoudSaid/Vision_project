import enum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from local_attendance.models import Base, TimestampMixin, generate_uuid


class FacialReferenceQuality(str, enum.Enum):
    USABLE = "usable"
    REJECTED = "rejected"


class FacialReference(Base, TimestampMixin):
    __tablename__ = "facial_references"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False)
    embedding: Mapped[str] = mapped_column(Text, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    quality_status: Mapped[FacialReferenceQuality] = mapped_column(
        Enum(FacialReferenceQuality, native_enum=False), nullable=False
    )
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("local_users.id"), nullable=False)
    replaced_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    employee: Mapped["Employee"] = relationship(back_populates="facial_references")  # noqa: F821
