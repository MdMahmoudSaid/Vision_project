import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from local_attendance.auth.password import hash_password
from local_attendance.auth.tokens import create_access_token
from local_attendance.camera.base import CameraBase, CameraCaptureError, CapturedFrame, get_camera
from local_attendance.database import get_db
from local_attendance.face.engine import ComparisonResult, FaceEngineBase, get_face_engine
from local_attendance.main import app
from local_attendance.models import Base
from local_attendance.models.employee import Employee
from local_attendance.models.facial_reference import FacialReference, FacialReferenceQuality
from local_attendance.models.user import LocalUser, UserRole


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


class FakeCamera(CameraBase):
    def __init__(self) -> None:
        self.raise_error = False
        self.frame = CapturedFrame(image="fake-frame")

    def capture_frame(self) -> CapturedFrame:
        if self.raise_error:
            raise CameraCaptureError("camera unusable")
        return self.frame

    def encode_jpeg(self, frame: CapturedFrame) -> bytes:
        return b"fake-jpeg-bytes"


class FakeFaceEngine(FaceEngineBase):
    def __init__(self) -> None:
        self.enroll_returns_face = True
        self.enroll_embedding = [0.1, 0.2, 0.3]
        self.compare_is_match = True
        self.compare_similarity = 0.9
        self.raise_on_compare = False
        self.raise_reason = "face_not_detected"
        # When set, the first N calls to enroll_sample() report "no face"
        # before succeeding, to simulate a few transient bad frames.
        self.enroll_fail_first_n_calls = 0
        self._enroll_calls = 0

    def enroll_sample(self, frame: CapturedFrame) -> list[float] | None:
        self._enroll_calls += 1
        if self._enroll_calls <= self.enroll_fail_first_n_calls:
            return None
        if not self.enroll_returns_face:
            return None
        return self.enroll_embedding

    def compare(self, capture: CapturedFrame, reference_embedding: list[float]) -> ComparisonResult:
        if self.raise_on_compare:
            from local_attendance.face.engine import FaceEngineError

            raise FaceEngineError("No usable face detected in capture", reason=self.raise_reason)
        return ComparisonResult(is_match=self.compare_is_match, similarity_score=self.compare_similarity)


@pytest.fixture()
def fake_camera() -> FakeCamera:
    return FakeCamera()


@pytest.fixture()
def fake_face_engine() -> FakeFaceEngine:
    return FakeFaceEngine()


@pytest.fixture()
def client(db_session: Session, fake_camera: FakeCamera, fake_face_engine: FakeFaceEngine):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_camera] = lambda: fake_camera
    app.dependency_overrides[get_face_engine] = lambda: fake_face_engine
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _create_local_user(db_session: Session, username: str, password: str, role: UserRole, active: bool = True) -> LocalUser:
    user = LocalUser(username=username, password_hash=hash_password(password), role=role, active=active)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def admin_user(db_session: Session) -> LocalUser:
    return _create_local_user(db_session, "admin1", "adminpass123", UserRole.ADMIN)


@pytest.fixture()
def guard_user(db_session: Session) -> LocalUser:
    return _create_local_user(db_session, "guard1", "guardpass123", UserRole.GUARD)


def _auth_headers(user: LocalUser) -> dict[str, str]:
    token = create_access_token(subject=user.id, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_auth_headers(admin_user: LocalUser) -> dict[str, str]:
    return _auth_headers(admin_user)


@pytest.fixture()
def guard_auth_headers(guard_user: LocalUser) -> dict[str, str]:
    return _auth_headers(guard_user)


def _create_employee_with_face(
    db_session: Session,
    admin_user: LocalUser,
    full_name: str = "Jane Doe",
    employee_number: str = "EMP0001",
) -> Employee:
    employee = Employee(full_name=full_name, employee_number=employee_number)
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    reference = FacialReference(
        employee_id=employee.id,
        embedding=json.dumps([0.1, 0.2, 0.3]),
        sample_count=3,
        quality_status=FacialReferenceQuality.USABLE,
        created_by_user_id=admin_user.id,
    )
    db_session.add(reference)
    db_session.commit()
    db_session.refresh(employee)
    return employee


@pytest.fixture()
def employee_with_face(db_session: Session, admin_user: LocalUser) -> Employee:
    return _create_employee_with_face(db_session, admin_user)
