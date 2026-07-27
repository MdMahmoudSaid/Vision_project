from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from cloud_attendance.auth.tokens import create_access_token
from cloud_attendance.models import SyncedEmployee


def _make_employee(db_session: Session, **overrides) -> SyncedEmployee:
    defaults = dict(
        id=overrides.pop("id", "emp-list-1"),
        full_name="List Test",
        employee_number="L001",
        department="Engineering",
        active=True,
        has_face_reference=True,
    )
    defaults.update(overrides)
    employee = SyncedEmployee(**defaults)
    db_session.add(employee)
    db_session.commit()
    return employee


def test_list_employees_returns_synced_employees(client: TestClient, db_session: Session, viewer_auth_headers):
    _make_employee(db_session, id="emp-a", full_name="Alice", employee_number="A1")
    _make_employee(db_session, id="emp-b", full_name="Bob", employee_number="B1", active=False)

    response = client.get("/employees", headers=viewer_auth_headers)
    assert response.status_code == 200
    names = {e["full_name"] for e in response.json()}
    # Default active=True filter excludes the inactive employee.
    assert names == {"Alice"}


def test_list_employees_active_false_includes_inactive(client: TestClient, db_session: Session, admin_auth_headers):
    _make_employee(db_session, id="emp-c", full_name="Carol", employee_number="C1", active=False)

    response = client.get("/employees?active=false", headers=admin_auth_headers)
    assert response.status_code == 200
    names = {e["full_name"] for e in response.json()}
    assert "Carol" in names


def test_list_employees_query_filters_by_name_or_number(client: TestClient, db_session: Session, admin_auth_headers):
    _make_employee(db_session, id="emp-d", full_name="Dave", employee_number="D1")
    _make_employee(db_session, id="emp-e", full_name="Erin", employee_number="E1")

    response = client.get("/employees?query=Dave", headers=admin_auth_headers)
    assert response.status_code == 200
    names = {e["full_name"] for e in response.json()}
    assert names == {"Dave"}


def test_list_employees_rejects_guard_role(client: TestClient, db_session: Session):
    _make_employee(db_session)
    token = create_access_token(subject="guard-1", role="guard")

    response = client.get("/employees", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["error"] == "forbidden"


def test_list_employees_requires_authentication(client: TestClient):
    response = client.get("/employees")
    assert response.status_code == 401
