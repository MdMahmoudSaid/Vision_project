from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import jwt

from cloud_attendance.models.cloud_user import CloudUser, CloudRole
from cloud_attendance.auth.tokens import create_access_token
from cloud_attendance.config import get_settings


def test_login_success(client: TestClient, owner_user: CloudUser):
    response = client.post("/auth/login", json={"email": "owner@example.com", "password": "ownerpass123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "owner@example.com"
    assert data["user"]["role"] == "owner"


def test_login_invalid_password(client: TestClient, owner_user: CloudUser):
    response = client.post("/auth/login", json={"email": "owner@example.com", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_credentials"


def test_login_invalid_email(client: TestClient):
    response = client.post("/auth/login", json={"email": "nobody@example.com", "password": "password"})
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_credentials"


def test_login_inactive_account(client: TestClient, db_session: Session, owner_user: CloudUser):
    owner_user.active = False
    db_session.commit()
    
    response = client.post("/auth/login", json={"email": "owner@example.com", "password": "ownerpass123"})
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_credentials"


def test_guard_role_rejected(client: TestClient):
    # A Guard token might be issued by the local_attendance system using the SAME secret (if they share it).
    # We must ensure the cloud system rejects it explicitly.
    token = create_access_token(subject="user-1", role="guard")
    
    # We need a dummy endpoint to test dependency rejection. We'll use health? No, health has no auth.
    # Let's add a test-only route to test dependencies, or since we haven't implemented other endpoints yet,
    # we can just test the dependency directly or wait for users.py. But since US4 asks us to test this, 
    # we should add a small dummy route here in the test to ensure dependencies work.
    
    from fastapi import APIRouter, Depends
    from cloud_attendance.auth.dependencies import require_any_cloud_role
    from cloud_attendance.main import app
    
    test_router = APIRouter()
    @test_router.get("/test-auth", dependencies=[Depends(require_any_cloud_role)])
    def test_auth_endpoint():
        return {"ok": True}
        
    app.include_router(test_router)
    
    response = client.get("/test-auth", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["error"] == "forbidden"
