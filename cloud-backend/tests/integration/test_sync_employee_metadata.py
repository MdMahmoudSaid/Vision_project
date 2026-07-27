from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from cloud_attendance.config import get_settings
from cloud_attendance.models import SyncedEmployee


def test_sync_employee_metadata(client: TestClient, db_session: Session):
    settings = get_settings()
    settings.sync_api_keys = {"test-site": "test-secret-key"}
    
    payload = {
        "employees": [
            {
                "id": "emp-metadata-1",
                "full_name": "Metadata Test",
                "employee_number": "M001",
                "department": "Engineering",
                "active": True,
                "has_face_reference": True,
                "synced_at": "2026-07-27T10:00:00Z"
            }
        ],
        "verification_attempts": [],
        "attendance_events": []
    }
    
    response = client.post(
        "/sync/batch", 
        json=payload,
        headers={"X-Sync-Api-Key": "test-secret-key"}
    )
    assert response.status_code == 200
    
    employee = db_session.scalar(select(SyncedEmployee).where(SyncedEmployee.id == "emp-metadata-1"))
    assert employee is not None
    assert employee.full_name == "Metadata Test"
    assert employee.department == "Engineering"
    assert employee.has_face_reference is True
    
    # We assert it never accepts or stores a facial embedding field because it's not even
    # part of the SyncedEmployee model or the SyncBatchRequest schema.
    assert not hasattr(employee, "facial_references")
    assert not hasattr(employee, "embedding")


def test_sync_employee_metadata_update_applies_to_existing_row(client: TestClient, db_session: Session):
    """A second sync of the same employee id (e.g. after a local deactivation
    or department change) must update the existing cloud row, not silently
    no-op it — otherwise edits made after the first sync would never reach
    the cloud dashboard (spec FR-001, US1 acceptance scenario 4)."""
    settings = get_settings()
    settings.sync_api_keys = {"test-site": "test-secret-key"}
    headers = {"X-Sync-Api-Key": "test-secret-key"}

    first_payload = {
        "employees": [
            {
                "id": "emp-metadata-2",
                "full_name": "Before Update",
                "employee_number": "M002",
                "department": "Engineering",
                "active": True,
                "has_face_reference": False,
                "synced_at": "2026-07-27T10:00:00Z",
            }
        ],
        "verification_attempts": [],
        "attendance_events": [],
    }
    response = client.post("/sync/batch", json=first_payload, headers=headers)
    assert response.status_code == 200

    first = db_session.scalar(select(SyncedEmployee).where(SyncedEmployee.id == "emp-metadata-2"))
    first_synced_at = first.synced_at

    second_payload = {
        "employees": [
            {
                "id": "emp-metadata-2",
                "full_name": "Before Update",
                "employee_number": "M002",
                "department": "Sales",
                "active": False,
                "has_face_reference": True,
                "synced_at": "2026-07-27T10:00:00Z",
            }
        ],
        "verification_attempts": [],
        "attendance_events": [],
    }
    response = client.post("/sync/batch", json=second_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["employees_accepted"] == 1

    db_session.expire_all()
    updated = db_session.scalar(select(SyncedEmployee).where(SyncedEmployee.id == "emp-metadata-2"))
    assert updated is not None
    assert updated.department == "Sales"
    assert updated.active is False
    assert updated.has_face_reference is True
    # synced_at must be the cloud's own ingestion timestamp, not whatever the
    # client sent (both payloads sent the identical client-side value above).
    assert updated.synced_at > first_synced_at

    # Still exactly one row for this id — an update, not a duplicate insert.
    count = db_session.scalar(
        select(SyncedEmployee.id).where(SyncedEmployee.id == "emp-metadata-2")
    )
    all_rows = db_session.scalars(
        select(SyncedEmployee).where(SyncedEmployee.id == "emp-metadata-2")
    ).all()
    assert len(all_rows) == 1
