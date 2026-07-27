from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from cloud_attendance.models import SyncedAttendanceEvent, SyncedEmployee
from cloud_attendance.models.synced_verification_attempt import SyncedAttendanceType


def _make_employee(db_session: Session, employee_id: str = "emp-nondest-1") -> SyncedEmployee:
    employee = SyncedEmployee(
        id=employee_id,
        full_name="Non Destructive Target",
        employee_number="ND1",
        active=True,
        has_face_reference=False,
    )
    db_session.add(employee)
    db_session.commit()
    return employee


def test_correction_preserves_original_event_and_report_shows_corrected_value(
    client: TestClient, db_session: Session, admin_auth_headers
):
    employee = _make_employee(db_session)
    event = SyncedAttendanceEvent(
        id="evt-nondest-1",
        employee_id=employee.id,
        type=SyncedAttendanceType.ARRIVAL,
        timestamp=datetime(2026, 7, 27, 8, 0, 0, tzinfo=timezone.utc),
        verification_attempt_id="attempt-nondest-1",
    )
    db_session.add(event)
    db_session.commit()

    response = client.post(
        "/attendance/corrections",
        json={
            "employee_id": employee.id,
            "attendance_event_id": event.id,
            "action": "correct_time",
            "new_value": {"timestamp": "2026-07-27T08:45:00Z"},
            "reason": "NVR shows the real arrival time",
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 201

    # The original synced event is untouched — the correction is a separate,
    # append-only record layered on top of it, never an in-place edit.
    db_session.expire_all()
    original = db_session.scalar(select(SyncedAttendanceEvent).where(SyncedAttendanceEvent.id == "evt-nondest-1"))
    assert original.timestamp.replace(tzinfo=timezone.utc) == datetime(2026, 7, 27, 8, 0, 0, tzinfo=timezone.utc)

    # But the report reflects the corrected value, flagged as corrected.
    report_response = client.get("/reports/daily?date=2026-07-27", headers=admin_auth_headers)
    assert report_response.status_code == 200
    rows = report_response.json()["rows"]
    assert len(rows) == 1
    assert rows[0]["arrival_time"] == "2026-07-27T08:45:00Z"
    assert rows[0]["corrected"] is True
