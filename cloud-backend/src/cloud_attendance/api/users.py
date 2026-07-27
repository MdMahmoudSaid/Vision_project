from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from cloud_attendance.auth.dependencies import require_owner
from cloud_attendance.database import get_db
from cloud_attendance.models.cloud_user import CloudUser
from cloud_attendance.schemas.auth import CloudUser as CloudUserSchema
from cloud_attendance.schemas.user import CloudUserInvite, CloudUserUpdate
from cloud_attendance.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[CloudUserSchema])
def list_users(
    db: Session = Depends(get_db),
    _: CloudUser = Depends(require_owner),
) -> list[CloudUser]:
    return user_service.list_users(db)


@router.post("", response_model=CloudUserSchema, status_code=status.HTTP_201_CREATED)
def invite_user(
    payload: CloudUserInvite,
    db: Session = Depends(get_db),
    current_user: CloudUser = Depends(require_owner),
) -> CloudUser:
    return user_service.invite_user(db, payload, invited_by=current_user.id)


@router.patch("/{user_id}", response_model=CloudUserSchema)
def update_user(
    user_id: str,
    payload: CloudUserUpdate,
    db: Session = Depends(get_db),
    _: CloudUser = Depends(require_owner),
) -> CloudUser:
    return user_service.update_user(db, user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: CloudUser = Depends(require_owner),
) -> None:
    user_service.delete_user(db, user_id, current_user_id=current_user.id)
