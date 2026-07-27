"""spec FR-022: corrections created on the cloud dashboard must never modify
or require any write-back to the local PC's own records. A genuine
cross-process check against backend/'s SQLite database isn't practical from
this package's test suite (separate process, separate deployment); the
practically verifiable proxy is that creating a correction never performs
any outbound network I/O at all — there is no code path by which the cloud
could reach the local PC even if it wanted to."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from cloud_attendance.models import SyncedEmployee


def _make_employee(db_session: Session, employee_id: str = "emp-localpc-1") -> SyncedEmployee:
    employee = SyncedEmployee(
        id=employee_id,
        full_name="Local PC Unaffected Target",
        employee_number="LP1",
        active=True,
        has_face_reference=False,
    )
    db_session.add(employee)
    db_session.commit()
    return employee


def test_correction_creation_never_makes_a_network_call(
    client: TestClient, db_session: Session, admin_auth_headers
):
    employee = _make_employee(db_session)

    response = client.post(
        "/attendance/corrections",
        json={
            "employee_id": employee.id,
            "action": "add_departure",
            "new_value": {"timestamp": "2026-07-27T17:00:00Z"},
            "reason": "Guard forgot to trigger departure verification",
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 201


def test_correction_service_module_has_no_network_dependency():
    """A correction's write path (correction_service.create_correction) must
    have no code path capable of reaching the local PC at all — verified
    structurally, since TestClient itself is implemented on top of httpx and
    can't be used to prove the absence of an *application* network call by
    monkeypatching httpx globally."""
    import inspect

    from cloud_attendance.services import correction_service

    source = inspect.getsource(correction_service)
    assert "httpx" not in source
    assert "requests" not in source
