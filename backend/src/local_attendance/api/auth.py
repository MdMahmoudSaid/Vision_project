from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from local_attendance.auth.password import hash_password, verify_password
from local_attendance.auth.tokens import create_access_token
from local_attendance.database import get_db
from local_attendance.models.user import LocalUser
from local_attendance.schemas.auth import LocalUser as LocalUserSchema
from local_attendance.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Verified on every login attempt, even for unknown usernames, so that
# bcrypt's deliberately-slow hashing runs with the same timing whether or not
# the account exists. Without this, verify_password is only reached for real
# usernames, and the timing gap lets an attacker enumerate valid accounts.
_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-constant-time-login")


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.scalar(select(LocalUser).where(LocalUser.username == payload.username))
    password_hash = user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
    password_ok = verify_password(payload.password, password_hash)

    if user is None or not user.active or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "message": "Invalid credentials or inactive account"},
        )

    token = create_access_token(subject=user.id, role=user.role.value)
    return LoginResponse(access_token=token, user=LocalUserSchema.model_validate(user))
