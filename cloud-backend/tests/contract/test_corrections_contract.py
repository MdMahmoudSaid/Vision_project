from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from cloud_attendance.models import SyncedAttendanceEvent, SyncedEmployee
from cloud_attendance.models.synced_verification_attempt import SyncedAttendanceType
from datetime import datetime, timezone


def _make_employee(db_session: Session, employee_id: str = "emp-corr-1") -> SyncedEmployee:
    employee = SyncedEmployee(
        id=employee_id,
        full_name="Correction Target",
        employee_number="CO1",
        active=True,
        has_face_reference=False,
    )
    db_session.add(employee)
    db_session.commit()
    return employee


def _make_event(db_session: Session, employee_id: str, event_id: str = "evt-corr-1") -> SyncedAttendanceEvent:
    event = SyncedAttendanceEvent(
        id=event_id,
        employee_id=employee_id,
        type=SyncedAttendanceType.ARRIVAL,
        timestamp=datetime(2026, 7, 27, 8, 0, 0, tzinfo=timezone.utc),
        verification_attempt_id="attempt-1",
    )
    db_session.add(event)
    db_session.commit()
    return event


def test_add_arrival_correction_succeeds(client: TestClient, db_session: Session, admin_auth_headers):
    _make_employee(db_session)
    response = client.post(
        "/attendance/corrections",
        json={
            "employee_id": "emp-corr-1",
            "action": "add_arrival",
            "new_value": {"timestamp": "2026-07-27T08:00:00Z"},
            "reason": "Guard forgot to trigger verification",
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["action"] == "add_arrival"
    assert body["attendance_event_id"] is None
    assert body["previous_value"] is None


def test_correction_missing_reason_returns_400(client: TestClient, db_session: Session, admin_auth_headers):
    _make_employee(db_session)
    response = client.post(
        "/attendance/corrections",
        json={
            "employee_id": "emp-corr-1",
            "action": "add_arrival",
            "new_value": {"timestamp": "2026-07-27T08:00:00Z"},
            "reason": "   ",
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 400


def test_add_arrival_with_attendance_event_id_returns_400(client: TestClient, db_session: Session, admin_auth_headers):
    employee = _make_employee(db_session)
    event = _make_event(db_session, employee.id)
    response = client.post(
        "/attendance/corrections",
        json={
            "employee_id": employee.id,
            "attendance_event_id": event.id,
            "action": "add_arrival",
            "new_value": {"timestamp": "2026-07-27T08:00:00Z"},
            "reason": "Should not reference an existing event",
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 400


def test_correct_time_without_attendance_event_id_returns_400(client: TestClient, db_session: Session, admin_auth_headers):
    _make_employee(db_session)
    response = client.post(
        "/attendance/corrections",
        json={
            "employee_id": "emp-corr-1",
            "action": "correct_time",
            "new_value": {"timestamp": "2026-07-27T08:30:00Z"},
            "reason": "Must reference an existing event",
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 400


def test_correct_time_on_existing_event_succeeds(client: TestClient, db_session: Session, admin_auth_headers):
    employee = _make_employee(db_session)
    event = _make_event(db_session, employee.id)
    response = client.post(
        "/attendance/corrections",
        json={
            "employee_id": employee.id,
            "attendance_event_id": event.id,
            "action": "correct_time",
            "new_value": {"timestamp": "2026-07-27T08:30:00Z"},
            "reason": "NVR shows a different arrival time",
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["previous_value"] == {"timestamp": "2026-07-27T08:00:00+00:00"}
    assert body["new_value"] == {"timestamp": "2026-07-27T08:30:00Z"}


def test_correction_viewer_forbidden(client: TestClient, db_session: Session, viewer_auth_headers):
    _make_employee(db_session)
    response = client.post(
        "/attendance/corrections",
        json={
            "employee_id": "emp-corr-1",
            "action": "add_arrival",
            "new_value": {"timestamp": "2026-07-27T08:00:00Z"},
            "reason": "Viewer should not be allowed",
        },
        headers=viewer_auth_headers,
    )
    assert response.status_code == 403
