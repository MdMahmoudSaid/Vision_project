from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from local_attendance.auth.tokens import TokenError, decode_access_token
from local_attendance.database import get_db
from local_attendance.models.user import LocalUser, UserRole

_bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "unauthorized", "message": message},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> LocalUser:
    if credentials is None:
        raise _unauthorized("Not authenticated")

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise _unauthorized("Invalid or expired token") from exc

    user = db.get(LocalUser, payload.get("sub"))
    if user is None or not user.active:
        raise _unauthorized("Invalid or inactive user")
    return user


def require_admin(current_user: LocalUser = Depends(get_current_user)) -> LocalUser:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "Admin role required"},
        )
    return current_user


def require_guard_or_admin(current_user: LocalUser = Depends(get_current_user)) -> LocalUser:
    if current_user.role not in (UserRole.ADMIN, UserRole.GUARD):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "Guard or admin role required"},
        )
    return current_user
