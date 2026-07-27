from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from cloud_attendance.models import SyncedAttendanceEvent, SyncedEmployee
from cloud_attendance.models.synced_verification_attempt import SyncedAttendanceType


def _make_employee(db_session: Session, employee_id: str = "emp-audit-1") -> SyncedEmployee:
    employee = SyncedEmployee(
        id=employee_id,
        full_name="Audit Target",
        employee_number="AU1",
        active=True,
        has_face_reference=False,
    )
    db_session.add(employee)
    db_session.commit()
    return employee


def _make_event(db_session: Session, employee_id: str, event_id: str = "evt-audit-1") -> SyncedAttendanceEvent:
    event = SyncedAttendanceEvent(
        id=event_id,
        employee_id=employee_id,
        type=SyncedAttendanceType.ARRIVAL,
        timestamp=datetime(2026, 7, 27, 8, 0, 0, tzinfo=timezone.utc),
        verification_attempt_id="attempt-audit-1",
    )
    db_session.add(event)
    db_session.commit()
    return event


def test_audit_trail_returns_corrections_in_order(client: TestClient, db_session: Session, admin_auth_headers):
    employee = _make_employee(db_session)
    event = _make_event(db_session, employee.id)

    client.post(
        "/attendance/corrections",
        json={
            "employee_id": employee.id,
            "attendance_event_id": event.id,
            "action": "correct_time",
            "new_value": {"timestamp": "2026-07-27T08:15:00Z"},
            "reason": "First correction",
        },
        headers=admin_auth_headers,
    )
    client.post(
        "/attendance/corrections",
        json={
            "employee_id": employee.id,
            "attendance_event_id": event.id,
            "action": "correct_time",
            "new_value": {"timestamp": "2026-07-27T08:30:00Z"},
            "reason": "Second correction",
        },
        headers=admin_auth_headers,
    )

    response = client.get(f"/attendance/corrections/{employee.id}", headers=admin_auth_headers)
    assert response.status_code == 200
    corrections = response.json()
    assert len(corrections) == 2
    assert corrections[0]["reason"] == "First correction"
    assert corrections[1]["reason"] == "Second correction"


def test_audit_trail_forbidden_for_viewer(client: TestClient, db_session: Session, viewer_auth_headers):
    employee = _make_employee(db_session)
    response = client.get(f"/attendance/corrections/{employee.id}", headers=viewer_auth_headers)
    assert response.status_code == 403
