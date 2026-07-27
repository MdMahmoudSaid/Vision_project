from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from cloud_attendance.models.cloud_user import CloudUser


def test_owner_can_change_user_role(client: TestClient, owner_auth_headers, admin_user: CloudUser):
    response = client.patch(
        f"/users/{admin_user.id}",
        json={"role": "viewer"},
        headers=owner_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["role"] == "viewer"


def test_owner_can_revoke_user_access(client: TestClient, owner_auth_headers, admin_user: CloudUser):
    response = client.patch(
        f"/users/{admin_user.id}",
        json={"active": False},
        headers=owner_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["active"] is False


def test_update_user_rejects_guard_role(client: TestClient, owner_auth_headers, admin_user: CloudUser):
    response = client.patch(
        f"/users/{admin_user.id}",
        json={"role": "guard"},
        headers=owner_auth_headers,
    )
    assert response.status_code == 422


def test_admin_cannot_update_users(client: TestClient, admin_auth_headers, viewer_user: CloudUser):
    response = client.patch(
        f"/users/{viewer_user.id}",
        json={"active": False},
        headers=admin_auth_headers,
    )
    assert response.status_code == 403


def test_update_unknown_user_returns_404(client: TestClient, owner_auth_headers):
    response = client.patch(
        "/users/does-not-exist",
        json={"active": False},
        headers=owner_auth_headers,
    )
    assert response.status_code == 404
