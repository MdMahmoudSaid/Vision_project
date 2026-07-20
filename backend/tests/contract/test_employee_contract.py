from local_attendance.models.employee import Employee


def test_list_employees_contract_shape(client, guard_auth_headers, employee_with_face):
    response = client.get("/employees", headers=guard_auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert set(body[0].keys()) == {
        "id",
        "full_name",
        "employee_number",
        "department",
        "active",
        "has_face_reference",
    }


def test_create_employee_contract_shape(client, admin_auth_headers):
    response = client.post("/employees", json={"full_name": "New Person"}, headers=admin_auth_headers)
    assert response.status_code == 201
    expected_keys = {
        "id",
        "full_name",
        "employee_number",
        "department",
        "active",
        "has_face_reference",
        "job_title",
        "phone",
        "notes",
        "registration_date",
        "created_at",
        "updated_at",
    }
    assert set(response.json().keys()) == expected_keys


def test_update_employee_contract_shape(client, admin_auth_headers, employee_with_face):
    response = client.patch(
        f"/employees/{employee_with_face.id}",
        json={"department": "Ops"},
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["department"] == "Ops"


def test_enroll_face_contract_shape(client, admin_auth_headers, db_session):
    employee = Employee(full_name="Face Target", employee_number="EMP7777")
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    response = client.post(
        f"/employees/{employee.id}/face",
        json={"sample_count": 2},
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"employee_id", "status", "sample_count", "enrolled_at"}
    assert body["status"] == "usable"
    assert body["sample_count"] == 2
