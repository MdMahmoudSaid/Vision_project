from typing import List

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cloud_attendance.auth.password import hash_password
from cloud_attendance.models.cloud_user import CloudRole, CloudUser
from cloud_attendance.models.correction import Correction
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


def delete_user(db: Session, user_id: str, current_user_id: str) -> None:
    user = db.get(CloudUser, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "user_not_found", "message": f"Cloud user {user_id} not found"},
        )

    if user.id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "cannot_delete_self", "message": "You cannot delete your own account"},
        )

    if user.role == CloudRole.owner:
        remaining_owners = db.scalar(
            select(func.count())
            .select_from(CloudUser)
            .where(CloudUser.role == CloudRole.owner, CloudUser.id != user.id)
        )
        if not remaining_owners:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "last_owner",
                    "message": "Cannot delete the last remaining Owner account",
                },
            )

    has_corrections = db.scalar(select(Correction.id).where(Correction.performed_by == user.id).limit(1))
    if has_corrections is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "user_has_corrections",
                "message": (
                    "This user has made corrections that must remain in the audit trail "
                    "and cannot be deleted; deactivate the account instead"
                ),
            },
        )

    db.delete(user)
    db.commit()
