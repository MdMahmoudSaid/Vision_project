from local_attendance.models.employee import Employee
from local_attendance.models.facial_reference import FacialReference
from local_attendance.models.verification_attempt import VerificationAttempt


def test_face_enrollment_creates_usable_reference(client, admin_auth_headers, db_session):
    employee = Employee(full_name="Enroll Me", employee_number="EMP5001")
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    response = client.post(f"/employees/{employee.id}/face", headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "usable"

    references = db_session.query(FacialReference).filter_by(employee_id=employee.id).all()
    assert len(references) == 1
    assert references[0].replaced_at is None


def test_face_reenrollment_replaces_previous_reference_without_deleting_history(
    client, admin_auth_headers, guard_auth_headers, db_session
):
    employee = Employee(full_name="Re Enroll", employee_number="EMP5002")
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    client.post(f"/employees/{employee.id}/face", headers=admin_auth_headers)
    client.post(
        "/attendance/verify",
        json={"employee_id": employee.id, "type": "arrival"},
        headers=guard_auth_headers,
    )

    response = client.post(f"/employees/{employee.id}/face", headers=admin_auth_headers)
    assert response.status_code == 200

    references = db_session.query(FacialReference).filter_by(employee_id=employee.id).all()
    assert len(references) == 2
    assert sum(1 for ref in references if ref.replaced_at is not None) == 1
    assert sum(1 for ref in references if ref.replaced_at is None) == 1

    attempts = db_session.query(VerificationAttempt).filter_by(employee_id=employee.id).all()
    assert len(attempts) == 1


def test_face_enrollment_rejects_unusable_capture(client, admin_auth_headers, db_session, fake_face_engine):
    employee = Employee(full_name="Bad Capture", employee_number="EMP5003")
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    fake_face_engine.enroll_usable = False

    response = client.post(f"/employees/{employee.id}/face", headers=admin_auth_headers)
    assert response.status_code == 400
    assert response.json()["error"] == "capture_unusable"

    references = db_session.query(FacialReference).filter_by(employee_id=employee.id).all()
    assert references == []
