from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from cloud_attendance.auth.password import hash_password
from cloud_attendance.models.cloud_user import CloudUser
from cloud_attendance.schemas.user import CloudUserInvite, CloudUserUpdate


def list_users(db: Session) -> List[CloudUser]:
    return list(db.scalars(select(CloudUser).order_by(CloudUser.email)).all())


def invite_user(db: Session, payload: CloudUserInvite, invited_by: str) -> CloudUser:
    existing = db.scalar(select(CloudUser).where(CloudUser.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "email_already_exists", "message": f"A cloud user with email {payload.email} already exists"},
        )

    user = CloudUser(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        active=True,
        invited_by=invited_by,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: str, payload: CloudUserUpdate) -> CloudUser:
    user = db.get(CloudUser, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "user_not_found", "message": f"Cloud user {user_id} not found"},
        )

    if payload.role is not None:
        user.role = payload.role
    if payload.active is not None:
        user.active = payload.active

    db.commit()
    db.refresh(user)
    return user
