from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from local_attendance.auth.password import verify_password
from local_attendance.auth.tokens import create_access_token
from local_attendance.database import get_db
from local_attendance.models.user import LocalUser
from local_attendance.schemas.auth import LocalUser as LocalUserSchema
from local_attendance.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.scalar(select(LocalUser).where(LocalUser.username == payload.username))
    if user is None or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "message": "Invalid credentials or inactive account"},
        )

    token = create_access_token(subject=user.id, role=user.role.value)
    return LoginResponse(access_token=token, user=LocalUserSchema.model_validate(user))
