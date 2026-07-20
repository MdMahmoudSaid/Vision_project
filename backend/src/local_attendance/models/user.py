import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from local_attendance.models import Base, TimestampMixin, generate_uuid


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    GUARD = "guard"


class LocalUser(Base, TimestampMixin):
    __tablename__ = "local_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, native_enum=False), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
