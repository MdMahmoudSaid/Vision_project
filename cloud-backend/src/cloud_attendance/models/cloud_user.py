import enum
from typing import Optional

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from cloud_attendance.models import Base, TimestampMixin, generate_uuid


class CloudRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    viewer = "viewer"


class CloudUser(Base, TimestampMixin):
    __tablename__ = "cloud_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[CloudRole] = mapped_column(Enum(CloudRole, native_enum=False), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    invited_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
