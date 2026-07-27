from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from cloud_attendance.models.cloud_user import CloudRole
from cloud_attendance.schemas.auth import CloudUser


class CloudUserInvite(BaseModel):
    email: EmailStr
    role: CloudRole
    password: str = Field(min_length=8)


class CloudUserUpdate(BaseModel):
    role: Optional[CloudRole] = None
    active: Optional[bool] = None


__all__ = ["CloudUserInvite", "CloudUserUpdate", "CloudUser"]
