from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from cloud_attendance.auth.tokens import TokenError, decode_access_token
from cloud_attendance.database import get_db
from cloud_attendance.models.cloud_user import CloudUser, CloudRole
from cloud_attendance.config import get_settings

_bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "unauthorized", "message": message},
    )


def _forbidden(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"error": "forbidden", "message": message},
    )


def get_current_cloud_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> CloudUser:
    if credentials is None:
        raise _unauthorized("Not authenticated")

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise _unauthorized("Invalid or expired token") from exc

    # Reject anything that isn't explicitly one of the cloud roles (e.g. guard from local PC)
    role_str = payload.get("role")
    if role_str not in ("owner", "admin", "viewer"):
        raise _forbidden("Role not permitted in cloud dashboard")

    user = db.get(CloudUser, payload.get("sub"))
    if user is None or not user.active:
        raise _unauthorized("Invalid or inactive user")
    return user


def require_owner(current_user: CloudUser = Depends(get_current_cloud_user)) -> CloudUser:
    if current_user.role != CloudRole.owner:
        raise _forbidden("Owner role required")
    return current_user


def require_admin_or_owner(current_user: CloudUser = Depends(get_current_cloud_user)) -> CloudUser:
    if current_user.role not in (CloudRole.owner, CloudRole.admin):
        raise _forbidden("Admin or Owner role required")
    return current_user


def require_any_cloud_role(current_user: CloudUser = Depends(get_current_cloud_user)) -> CloudUser:
    if current_user.role not in (CloudRole.owner, CloudRole.admin, CloudRole.viewer):
        raise _forbidden("Cloud role required")
    return current_user


def require_sync_api_key(
    x_sync_api_key: str | None = Header(None, alias="X-Sync-Api-Key")
) -> str:
    if not x_sync_api_key:
        raise _unauthorized("Missing X-Sync-Api-Key header")
    
    settings = get_settings()
    # Find the site_id that matches this api key
    site_id = None
    for sid, key in settings.sync_api_keys.items():
        if key == x_sync_api_key:
            site_id = sid
            break
            
    if site_id is None:
        raise _unauthorized("Invalid API key")
        
    return site_id
