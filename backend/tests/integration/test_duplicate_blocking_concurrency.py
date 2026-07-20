import threading

from sqlalchemy.orm import sessionmaker

from local_attendance.auth.password import hash_password
from local_attendance.models.attendance_event import AttendanceEvent
from local_attendance.models.employee import Employee
from local_attendance.models.facial_reference import FacialReference, FacialReferenceQuality
from local_attendance.models.user import LocalUser, UserRole
from local_attendance.models.verification_attempt import AttendanceType
from local_attendance.services.verification_service import verify_attendance
from tests.conftest import FakeCamera, FakeFaceEngine


def test_concurrent_verify_calls_create_only_one_attendance_event(db_engine):
    """Regression test: two near-simultaneous verify_attendance calls for the
    same employee/type must not both pass the duplicate check before either
    commits. Uses two independent DB sessions on separate threads, the way two
    concurrent FastAPI requests would (each request gets its own session).
    """
    session_factory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    setup_session = session_factory()

    admin = LocalUser(username="race-admin", password_hash=hash_password("adminpass123"), role=UserRole.ADMIN)
    employee = Employee(full_name="Race Condition", employee_number="EMP-RACE")
    setup_session.add_all([admin, employee])
    setup_session.commit()
    setup_session.refresh(admin)
    setup_session.refresh(employee)

    reference = FacialReference(
        employee_id=employee.id,
        embedding="[0.1, 0.2, 0.3]",
        sample_count=3,
        quality_status=FacialReferenceQuality.USABLE,
        created_by_user_id=admin.id,
    )
    setup_session.add(reference)
    setup_session.commit()

    employee_id = employee.id
    admin_id = admin.id
    setup_session.close()

    results: list[str] = []

    def run_verify() -> None:
        session = session_factory()
        try:
            outcome = verify_attendance(
                db=session,
                employee_id=employee_id,
                type_requested=AttendanceType.ARRIVAL,
                guard=session.get(LocalUser, admin_id),
                camera=FakeCamera(),
                face_engine=FakeFaceEngine(),
            )
            results.append(outcome.status)
        finally:
            session.close()

    threads = [threading.Thread(target=run_verify) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    verify_session = session_factory()
    events = verify_session.query(AttendanceEvent).filter_by(employee_id=employee_id).all()
    verify_session.close()

    assert len(events) == 1
    assert sorted(results) == ["duplicate_blocked", "success"]
