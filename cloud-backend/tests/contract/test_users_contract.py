from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from cloud_attendance.models.cloud_user import CloudUser


def test_owner_can_list_users(client: TestClient, owner_auth_headers, owner_user: CloudUser):
    response = client.get("/users", headers=owner_auth_headers)
    assert response.status_code == 200
    emails = {u["email"] for u in response.json()}
    assert "owner@example.com" in emails


def test_admin_cannot_list_users(client: TestClient, admin_auth_headers):
    response = client.get("/users", headers=admin_auth_headers)
    assert response.status_code == 403


def test_viewer_cannot_list_users(client: TestClient, viewer_auth_headers):
    response = client.get("/users", headers=viewer_auth_headers)
    assert response.status_code == 403


def test_owner_can_invite_new_user(client: TestClient, owner_auth_headers, db_session: Session):
    response = client.post(
        "/users",
        json={"email": "new-admin@example.com", "role": "admin", "password": "supersecret1"},
        headers=owner_auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new-admin@example.com"
    assert body["role"] == "admin"
    assert body["active"] is True


def test_admin_cannot_invite_new_user(client: TestClient, admin_auth_headers):
    response = client.post(
        "/users",
        json={"email": "should-fail@example.com", "role": "viewer", "password": "supersecret1"},
        headers=admin_auth_headers,
    )
    assert response.status_code == 403


def test_invite_rejects_duplicate_email(client: TestClient, owner_auth_headers, owner_user: CloudUser):
    response = client.post(
        "/users",
        json={"email": "owner@example.com", "role": "admin", "password": "supersecret1"},
        headers=owner_auth_headers,
    )
    assert response.status_code == 409


def test_invite_rejects_guard_role(client: TestClient, owner_auth_headers):
    response = client.post(
        "/users",
        json={"email": "guard-attempt@example.com", "role": "guard", "password": "supersecret1"},
        headers=owner_auth_headers,
    )
    # Rejected by schema validation — "guard" isn't a valid CloudRole value at all.
    assert response.status_code == 422
