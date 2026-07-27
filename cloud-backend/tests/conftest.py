import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from cloud_attendance.auth.password import hash_password
from cloud_attendance.auth.tokens import create_access_token
from cloud_attendance.database import get_db
from cloud_attendance.main import app
from cloud_attendance.models import Base
from cloud_attendance.models.cloud_user import CloudUser, CloudRole


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session(db_engine):
    testing_session_local = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _create_cloud_user(db_session: Session, email: str, password: str, role: CloudRole, active: bool = True) -> CloudUser:
    user = CloudUser(email=email, password_hash=hash_password(password), role=role, active=active)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def owner_user(db_session: Session) -> CloudUser:
    return _create_cloud_user(db_session, "owner@example.com", "ownerpass123", CloudRole.owner)


@pytest.fixture()
def admin_user(db_session: Session) -> CloudUser:
    return _create_cloud_user(db_session, "admin@example.com", "adminpass123", CloudRole.admin)


@pytest.fixture()
def viewer_user(db_session: Session) -> CloudUser:
    return _create_cloud_user(db_session, "viewer@example.com", "viewerpass123", CloudRole.viewer)


def _auth_headers(user: CloudUser) -> dict[str, str]:
    token = create_access_token(subject=user.id, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def owner_auth_headers(owner_user: CloudUser) -> dict[str, str]:
    return _auth_headers(owner_user)


@pytest.fixture()
def admin_auth_headers(admin_user: CloudUser) -> dict[str, str]:
    return _auth_headers(admin_user)


@pytest.fixture()
def viewer_auth_headers(viewer_user: CloudUser) -> dict[str, str]:
    return _auth_headers(viewer_user)
