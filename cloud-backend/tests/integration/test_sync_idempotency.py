from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from cloud_attendance.config import get_settings
from cloud_attendance.models import SyncedEmployee


def test_sync_idempotency(client: TestClient, db_session: Session):
    settings = get_settings()
    settings.sync_api_keys = {"test-site": "test-secret-key"}
    
    payload = {
        "employees": [
            {
                "id": "emp-1",
                "full_name": "John Doe",
                "employee_number": "E001",
                "department": "Engineering",
                "active": True,
                "has_face_reference": True,
                "synced_at": "2026-07-27T10:00:00Z"
            }
        ],
        "verification_attempts": [],
        "attendance_events": []
    }
    
    # Push batch first time
    response1 = client.post(
        "/sync/batch", 
        json=payload,
        headers={"X-Sync-Api-Key": "test-secret-key"}
    )
    assert response1.status_code == 200
    assert response1.json()["employees_accepted"] == 1
    
    # Check DB
    count = db_session.scalar(select(SyncedEmployee).where(SyncedEmployee.id == "emp-1"))
    assert count is not None
    
    # Push batch second time
    response2 = client.post(
        "/sync/batch", 
        json=payload,
        headers={"X-Sync-Api-Key": "test-secret-key"}
    )
    assert response2.status_code == 200
    assert response2.json()["employees_accepted"] == 1 # Valid request, accepted again
    
    # Check DB again, should still be 1 row, not crash
    employees = db_session.scalars(select(SyncedEmployee).where(SyncedEmployee.id == "emp-1")).all()
    assert len(employees) == 1
