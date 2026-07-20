from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from local_attendance.models import AttendanceEvent, Employee, FacialReference, LocalUser, VerificationAttempt
from local_attendance.models.facial_reference import FacialReferenceQuality
from local_attendance.models.user import UserRole
from local_attendance.models.verification_attempt import AttendanceType, VerificationResult

BACKEND_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_TABLES = {
    "employees",
    "local_users",
    "facial_references",
    "verification_attempts",
    "attendance_events",
    "local_settings",
    "alembic_version",
}


def test_alembic_migration_creates_expected_schema(tmp_path):
    db_path = tmp_path / "migration_test.db"
    db_url = f"sqlite:///{db_path}"

    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", db_url)

    command.upgrade(config, "head")

    engine = create_engine(db_url)
    inspector = inspect(engine)
    assert EXPECTED_TABLES.issubset(set(inspector.get_table_names()))
    engine.dispose()


def test_model_relationships_navigate_correctly(db_session):
    admin = LocalUser(username="admin-rel", password_hash="hash", role=UserRole.ADMIN)
    employee = Employee(full_name="Jane Doe", employee_number="EMP0001")
    db_session.add_all([admin, employee])
    db_session.commit()

    reference = FacialReference(
        employee_id=employee.id,
        embedding="[0.1, 0.2]",
        sample_count=3,
        quality_status=FacialReferenceQuality.USABLE,
        created_by_user_id=admin.id,
    )
    db_session.add(reference)
    db_session.commit()

    attempt = VerificationAttempt(
        employee_id=employee.id,
        guard_id=admin.id,
        type_requested=AttendanceType.ARRIVAL,
        result=VerificationResult.SUCCESS,
        similarity_score=0.95,
    )
    db_session.add(attempt)
    db_session.commit()

    event = AttendanceEvent(
        employee_id=employee.id,
        type=AttendanceType.ARRIVAL,
        guard_id=admin.id,
        verification_attempt_id=attempt.id,
    )
    db_session.add(event)
    db_session.flush()
    attempt.attendance_event_id = event.id
    db_session.commit()
    db_session.refresh(employee)

    assert employee.facial_references[0].id == reference.id
    assert employee.verification_attempts[0].id == attempt.id
    assert employee.attendance_events[0].id == event.id
    assert event.verification_attempt.id == attempt.id
    assert attempt.attendance_event_id == event.id
