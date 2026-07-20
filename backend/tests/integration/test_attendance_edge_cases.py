from local_attendance.models.employee import Employee


def test_verify_requires_authentication(client, employee_with_face):
    response = client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
    )
    assert response.status_code == 401


def test_verify_rejects_inactive_employee(client, guard_auth_headers, employee_with_face, db_session):
    employee_with_face.active = False
    db_session.commit()

    response = client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["error"] == "employee_inactive"


def test_verify_rejects_missing_face_reference(client, guard_auth_headers, db_session):
    employee = Employee(full_name="No Face", employee_number="EMP9999")
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    response = client.post(
        "/attendance/verify",
        json={"employee_id": employee.id, "type": "arrival"},
        headers=guard_auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["error"] == "missing_reference"


def test_verify_rejects_unusable_camera_capture(client, guard_auth_headers, employee_with_face, fake_camera):
    fake_camera.raise_error = True

    response = client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["error"] == "capture_unusable"
