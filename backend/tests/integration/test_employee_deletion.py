from local_attendance.models.attendance_event import AttendanceEvent
from local_attendance.models.employee import Employee
from local_attendance.models.verification_attempt import AttendanceType, VerificationAttempt, VerificationResult


def test_admin_can_delete_employee_with_no_history(client, admin_auth_headers, db_session):
    employee = Employee(full_name="No History", employee_number="EMP-DEL-1")
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    response = client.delete(f"/employees/{employee.id}", headers=admin_auth_headers)
    assert response.status_code == 204

    assert db_session.get(Employee, employee.id) is None


def test_delete_blocked_when_employee_has_verification_history(
    client, admin_auth_headers, guard_user, db_session
):
    employee = Employee(full_name="Has History", employee_number="EMP-DEL-2")
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    attempt = VerificationAttempt(
        employee_id=employee.id,
        guard_id=guard_user.id,
        type_requested=AttendanceType.ARRIVAL,
        result=VerificationResult.FAILED,
        failure_reason="face_mismatch",
    )
    db_session.add(attempt)
    db_session.commit()

    response = client.delete(f"/employees/{employee.id}", headers=admin_auth_headers)
    assert response.status_code == 409
    assert response.json()["error"] == "employee_has_history"

    # employee and their history must both still exist
    assert db_session.get(Employee, employee.id) is not None
    assert db_session.get(VerificationAttempt, attempt.id) is not None


def test_delete_blocked_when_employee_has_attendance_event(client, admin_auth_headers, guard_user, db_session):
    employee = Employee(full_name="Has Event", employee_number="EMP-DEL-3")
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    attempt = VerificationAttempt(
        employee_id=employee.id,
        guard_id=guard_user.id,
        type_requested=AttendanceType.ARRIVAL,
        result=VerificationResult.SUCCESS,
    )
    db_session.add(attempt)
    db_session.flush()
    event = AttendanceEvent(
        employee_id=employee.id,
        type=AttendanceType.ARRIVAL,
        guard_id=guard_user.id,
        verification_attempt_id=attempt.id,
    )
    db_session.add(event)
    db_session.commit()

    response = client.delete(f"/employees/{employee.id}", headers=admin_auth_headers)
    assert response.status_code == 409


def test_delete_not_found_returns_404(client, admin_auth_headers):
    response = client.delete("/employees/00000000-0000-0000-0000-000000000000", headers=admin_auth_headers)
    assert response.status_code == 404


def test_guard_cannot_delete_employee(client, guard_auth_headers, employee_with_face):
    response = client.delete(f"/employees/{employee_with_face.id}", headers=guard_auth_headers)
    assert response.status_code == 403
