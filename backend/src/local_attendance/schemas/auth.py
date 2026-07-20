from pydantic import BaseModel, ConfigDict

from local_attendance.models.user import UserRole


class LoginRequest(BaseModel):
    username: str
    password: str


class LocalUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    role: UserRole


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: LocalUser
