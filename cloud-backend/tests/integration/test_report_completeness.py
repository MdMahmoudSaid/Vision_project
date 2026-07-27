from datetime import date, datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from cloud_attendance.models import SyncedEmployee, SyncedAttendanceEvent, SyncIngestLog
from cloud_attendance.models.synced_verification_attempt import SyncedAttendanceType


def test_report_completeness_matching(client: TestClient, db_session: Session, admin_auth_headers: dict):
    # Setup employee
    emp = SyncedEmployee(
        id="emp-completeness-1",
        full_name="Completeness Bob",
        employee_number="C001",
        department="Engineering",
        active=True,
        has_face_reference=True,
    )
    db_session.add(emp)
    
    # 1. Unmatched Arrival -> missing_departure
    evt_arr = SyncedAttendanceEvent(
        id="evt-arr",
        employee_id=emp.id,
        type=SyncedAttendanceType.ARRIVAL,
        timestamp=datetime(2026, 7, 27, 8, 0, 0, tzinfo=timezone.utc),
        verification_attempt_id="v-arr"
    )
    db_session.add(evt_arr)
    db_session.commit()
    
    response = client.get(
        "/reports/daily?date=2026-07-27",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert len(rows) == 1
    assert rows[0]["completeness"] == "missing_departure"
    
    # 2. Unmatched Departure -> missing_arrival
    db_session.delete(evt_arr)
    evt_dep = SyncedAttendanceEvent(
        id="evt-dep",
        employee_id=emp.id,
        type=SyncedAttendanceType.DEPARTURE,
        timestamp=datetime(2026, 7, 27, 17, 0, 0, tzinfo=timezone.utc),
        verification_attempt_id="v-dep"
    )
    db_session.add(evt_dep)
    db_session.commit()
    
    response = client.get(
        "/reports/daily?date=2026-07-27",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert rows[0]["completeness"] == "missing_arrival"
    
    # 3. Both -> complete
    evt_arr2 = SyncedAttendanceEvent(
        id="evt-arr-2",
        employee_id=emp.id,
        type=SyncedAttendanceType.ARRIVAL,
        timestamp=datetime(2026, 7, 27, 8, 0, 0, tzinfo=timezone.utc),
        verification_attempt_id="v-arr-2"
    )
    db_session.add(evt_arr2)
    db_session.commit()
    
    response = client.get(
        "/reports/daily?date=2026-07-27",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert rows[0]["completeness"] == "complete"
    assert rows[0]["worked_duration_minutes"] == 9 * 60 # 8:00 to 17:00 is 9 hours = 540 minutes


def test_report_may_be_incomplete(client: TestClient, db_session: Session, admin_auth_headers: dict):
    # Setup employee
    emp = SyncedEmployee(
        id="emp-incomplete-1",
        full_name="Incomplete User",
        employee_number="I001",
        active=True,
    )
    db_session.add(emp)
    
    # No sync logs yet, should be true
    response = client.get(
        "/reports/daily?date=2026-07-27",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    assert response.json()["may_be_incomplete"] is True
    
    # Setup sync log before the period's end (last sync at 2026-07-27 10:00:00)
    log = SyncIngestLog(
        timestamp=datetime(2026, 7, 27, 10, 0, 0, tzinfo=timezone.utc),
        success=True
    )
    db_session.add(log)
    db_session.commit()
    
    # Query for 2026-07-27. Since the period ends at 23:59:59 and last sync is 10:00:00,
    # it should be true.
    response = client.get(
        "/reports/daily?date=2026-07-27",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    assert response.json()["may_be_incomplete"] is True
    
    # Setup sync log after the period's end (last sync at 2026-07-28 02:00:00)
    log2 = SyncIngestLog(
        timestamp=datetime(2026, 7, 28, 2, 0, 0, tzinfo=timezone.utc),
        success=True
    )
    db_session.add(log2)
    db_session.commit()
    
    # Query for 2026-07-27. Period end is 23:59:59, last sync is 02:00:00 next day,
    # should be false.
    response = client.get(
        "/reports/daily?date=2026-07-27",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    assert response.json()["may_be_incomplete"] is False
