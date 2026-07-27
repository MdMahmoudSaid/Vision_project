from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from cloud_attendance.models import SyncedAttendanceEvent, SyncedEmployee
from cloud_attendance.models.synced_verification_attempt import SyncedAttendanceType


def test_employee_attendance_history_returns_days_in_range(client: TestClient, db_session: Session, admin_auth_headers):
    employee = SyncedEmployee(
        id="emp-history-1",
        full_name="History Target",
        employee_number="H001",
        active=True,
        has_face_reference=True,
    )
    db_session.add(employee)
    event = SyncedAttendanceEvent(
        id="evt-history-1",
        employee_id=employee.id,
        type=SyncedAttendanceType.ARRIVAL,
        timestamp=datetime(2026, 7, 27, 8, 0, 0, tzinfo=timezone.utc),
        verification_attempt_id="attempt-history-1",
    )
    db_session.add(event)
    db_session.commit()

    response = client.get(
        f"/employees/{employee.id}/attendance?date_from=2026-07-27&date_to=2026-07-27",
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["employee_id"] == employee.id
    assert body["employee_name"] == "History Target"
    assert len(body["days"]) == 1
    assert body["days"][0]["completeness"] == "missing_departure"


def test_employee_attendance_history_404_for_unknown_employee(client: TestClient, admin_auth_headers):
    response = client.get(
        "/employees/does-not-exist/attendance?date_from=2026-07-27&date_to=2026-07-27",
        headers=admin_auth_headers,
    )
    assert response.status_code == 404


def test_employee_attendance_history_forbidden_for_guard(client: TestClient, db_session: Session):
    from cloud_attendance.auth.tokens import create_access_token

    employee = SyncedEmployee(
        id="emp-history-2", full_name="Guard Blocked", employee_number="H002", active=True, has_face_reference=False
    )
    db_session.add(employee)
    db_session.commit()

    token = create_access_token(subject="guard-1", role="guard")
    response = client.get(
        f"/employees/{employee.id}/attendance",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
