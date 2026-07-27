from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from cloud_attendance.models import SyncedAttendanceEvent, SyncedEmployee
from cloud_attendance.models.synced_verification_attempt import SyncedAttendanceType


def test_two_corrections_to_same_event_both_appear_in_order(
    client: TestClient, db_session: Session, admin_auth_headers
):
    employee = SyncedEmployee(
        id="emp-chain-1",
        full_name="Chain Target",
        employee_number="CH1",
        active=True,
        has_face_reference=False,
    )
    db_session.add(employee)
    event = SyncedAttendanceEvent(
        id="evt-chain-1",
        employee_id=employee.id,
        type=SyncedAttendanceType.ARRIVAL,
        timestamp=datetime(2026, 7, 27, 8, 0, 0, tzinfo=timezone.utc),
        verification_attempt_id="attempt-chain-1",
    )
    db_session.add(event)
    db_session.commit()

    first = client.post(
        "/attendance/corrections",
        json={
            "employee_id": employee.id,
            "attendance_event_id": event.id,
            "action": "correct_time",
            "new_value": {"timestamp": "2026-07-27T08:15:00Z"},
            "reason": "First guess at the real time",
        },
        headers=admin_auth_headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/attendance/corrections",
        json={
            "employee_id": employee.id,
            "attendance_event_id": event.id,
            "action": "correct_time",
            "new_value": {"timestamp": "2026-07-27T08:20:00Z"},
            "reason": "Corrected again after reviewing NVR footage",
        },
        headers=admin_auth_headers,
    )
    assert second.status_code == 201

    # Both corrections remain visible in the audit trail, in order — the
    # second does not overwrite or remove the first.
    audit_response = client.get(f"/attendance/corrections/{employee.id}", headers=admin_auth_headers)
    assert audit_response.status_code == 200
    corrections = audit_response.json()
    assert len(corrections) == 2
    assert corrections[0]["new_value"] == {"timestamp": "2026-07-27T08:15:00Z"}
    assert corrections[1]["new_value"] == {"timestamp": "2026-07-27T08:20:00Z"}

    # But the report/history display uses only the latest correction's value.
    report_response = client.get("/reports/daily?date=2026-07-27", headers=admin_auth_headers)
    assert report_response.status_code == 200
    rows = report_response.json()["rows"]
    assert rows[0]["arrival_time"] == "2026-07-27T08:20:00Z"
