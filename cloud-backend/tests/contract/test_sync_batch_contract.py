from fastapi.testclient import TestClient

from cloud_attendance.config import get_settings


def test_sync_batch_contract_success(client: TestClient):
    settings = get_settings()
    settings.sync_api_keys = {"test-site": "test-secret-key"}
    
    payload = {
        "employees": [],
        "verification_attempts": [],
        "attendance_events": []
    }
    
    response = client.post(
        "/sync/batch", 
        json=payload,
        headers={"X-Sync-Api-Key": "test-secret-key"}
    )
    
    assert response.status_code == 200
    assert response.json() == {
        "employees_accepted": 0,
        "verification_attempts_accepted": 0,
        "attendance_events_accepted": 0,
    }


def test_sync_batch_missing_key(client: TestClient):
    payload = {
        "employees": [],
        "verification_attempts": [],
        "attendance_events": []
    }
    
    response = client.post("/sync/batch", json=payload)
    
    assert response.status_code == 401
    assert response.json()["error"] == "unauthorized"


def test_sync_batch_invalid_key(client: TestClient):
    settings = get_settings()
    settings.sync_api_keys = {"test-site": "test-secret-key"}
    
    payload = {
        "employees": [],
        "verification_attempts": [],
        "attendance_events": []
    }
    
    response = client.post(
        "/sync/batch", 
        json=payload,
        headers={"X-Sync-Api-Key": "invalid-secret-key"}
    )
    
    assert response.status_code == 401
    assert response.json()["error"] == "unauthorized"


def test_sync_batch_malformed_payload(client: TestClient):
    settings = get_settings()
    settings.sync_api_keys = {"test-site": "test-secret-key"}
    
    payload = {
        "employees": "not a list"
    }
    
    response = client.post(
        "/sync/batch", 
        json=payload,
        headers={"X-Sync-Api-Key": "test-secret-key"}
    )
    
    # FastAPI returns 422 for malformed payloads according to Pydantic models
    assert response.status_code == 422
