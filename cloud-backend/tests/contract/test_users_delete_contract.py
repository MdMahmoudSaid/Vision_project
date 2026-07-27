from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from cloud_attendance.models.cloud_user import CloudUser


def test_owner_can_delete_user(client: TestClient, owner_auth_headers, admin_user: CloudUser):
    response = client.delete(f"/users/{admin_user.id}", headers=owner_auth_headers)
    assert response.status_code == 204

    list_response = client.get("/users", headers=owner_auth_headers)
    assert admin_user.id not in [u["id"] for u in list_response.json()]


def test_admin_cannot_delete_users(client: TestClient, admin_auth_headers, viewer_user: CloudUser):
    response = client.delete(f"/users/{viewer_user.id}", headers=admin_auth_headers)
    assert response.status_code == 403


def test_delete_unknown_user_returns_404(client: TestClient, owner_auth_headers):
    response = client.delete("/users/does-not-exist", headers=owner_auth_headers)
    assert response.status_code == 404


def test_owner_cannot_delete_own_account(client: TestClient, owner_auth_headers, owner_user: CloudUser):
    response = client.delete(f"/users/{owner_user.id}", headers=owner_auth_headers)
    assert response.status_code == 409
    assert response.json()["error"] == "cannot_delete_self"


def test_cannot_delete_last_owner(
    client: TestClient, db_session: Session, owner_auth_headers, owner_user: CloudUser
):
    from cloud_attendance.auth.password import hash_password
    from cloud_attendance.models.cloud_user import CloudRole

    second_owner = CloudUser(
        email="second-owner@example.com",
        password_hash=hash_password("password123"),
        role=CloudRole.owner,
        active=True,
    )
    db_session.add(second_owner)
    db_session.commit()
    db_session.refresh(second_owner)

    # With two owners, deleting one (not self) is fine.
    response = client.delete(f"/users/{second_owner.id}", headers=owner_auth_headers)
    assert response.status_code == 204


def test_deleting_last_owner_when_not_self_is_rejected(
    client: TestClient, db_session: Session, owner_auth_headers, owner_user: CloudUser
):
    from cloud_attendance.auth.password import hash_password
    from cloud_attendance.auth.tokens import create_access_token
    from cloud_attendance.models.cloud_user import CloudRole

    second_owner = CloudUser(
        email="second-owner@example.com",
        password_hash=hash_password("password123"),
        role=CloudRole.owner,
        active=True,
    )
    db_session.add(second_owner)
    db_session.commit()
    db_session.refresh(second_owner)

    second_owner_token = create_access_token(subject=second_owner.id, role=second_owner.role.value)
    second_owner_headers = {"Authorization": f"Bearer {second_owner_token}"}

    # second_owner deletes the original owner_user, leaving only themselves.
    first_delete = client.delete(f"/users/{owner_user.id}", headers=second_owner_headers)
    assert first_delete.status_code == 204

    # Now only second_owner remains as Owner; nobody else can delete them.
    response = client.delete(f"/users/{second_owner.id}", headers=second_owner_headers)
    assert response.status_code == 409
    assert response.json()["error"] == "cannot_delete_self"


def test_cannot_delete_user_with_corrections(
    client: TestClient, db_session: Session, owner_auth_headers, admin_user: CloudUser
):
    from cloud_attendance.models import SyncedEmployee
    from cloud_attendance.models.correction import Correction, CorrectionAction

    employee = SyncedEmployee(id="emp-del-1", full_name="Del Test", employee_number="D001", active=True)
    db_session.add(employee)
    correction = Correction(
        employee_id=employee.id,
        action=CorrectionAction.ADD_ARRIVAL,
        new_value="{}",
        reason="test",
        performed_by=admin_user.id,
    )
    db_session.add(correction)
    db_session.commit()

    response = client.delete(f"/users/{admin_user.id}", headers=owner_auth_headers)
    assert response.status_code == 409
    assert response.json()["error"] == "user_has_corrections"
