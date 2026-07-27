from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from cloud_attendance.auth.tokens import create_access_token
from cloud_attendance.models.cloud_user import CloudUser


def test_revoked_user_denied_on_next_action_without_needing_to_log_in_again(
    client: TestClient, db_session: Session, owner_auth_headers, admin_user: CloudUser
):
    # admin_user already has a valid token, minted before revocation — this
    # simulates an already-active session.
    admin_token = create_access_token(subject=admin_user.id, role=admin_user.role.value)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Sanity check: the session works before revocation.
    ok_response = client.get("/employees", headers=admin_headers)
    assert ok_response.status_code == 200

    # Owner revokes access.
    revoke_response = client.patch(
        f"/users/{admin_user.id}",
        json={"active": False},
        headers=owner_auth_headers,
    )
    assert revoke_response.status_code == 200

    # The same, still-unexpired token must now be denied on its very next use.
    denied_response = client.get("/employees", headers=admin_headers)
    assert denied_response.status_code == 401
