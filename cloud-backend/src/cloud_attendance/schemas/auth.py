from pydantic import BaseModel, ConfigDict, EmailStr

from cloud_attendance.models.cloud_user import CloudRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CloudUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    role: CloudRole
    active: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: CloudUser
