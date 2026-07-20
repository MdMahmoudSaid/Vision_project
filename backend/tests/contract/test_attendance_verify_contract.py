def test_login_contract_success_shape(client, admin_user):
    response = client.post("/auth/login", json={"username": "admin1", "password": "adminpass123"})
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"access_token", "token_type", "user"}
    assert body["token_type"] == "bearer"
    assert set(body["user"].keys()) == {"id", "username", "role"}


def test_login_contract_error_shape(client, admin_user):
    response = client.post("/auth/login", json={"username": "admin1", "password": "wrong"})
    assert response.status_code == 401
    assert set(response.json().keys()) == {"error", "message"}


def test_attendance_verify_contract_success_shape(client, guard_auth_headers, employee_with_face):
    response = client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert {"result", "verification_attempt", "attendance_event"}.issubset(body.keys())
    assert set(body["verification_attempt"].keys()) == {
        "id",
        "employee_id",
        "guard_id",
        "type_requested",
        "timestamp",
        "result",
        "similarity_score",
        "failure_reason",
        "attendance_event_id",
    }
    assert body["attendance_event"] is not None
    assert set(body["attendance_event"].keys()) == {
        "id",
        "employee_id",
        "guard_id",
        "type",
        "timestamp",
        "verification_attempt_id",
        "source",
    }


def test_attendance_verify_contract_error_shape(client, guard_auth_headers):
    response = client.post(
        "/attendance/verify",
        json={"employee_id": "00000000-0000-0000-0000-000000000000", "type": "arrival"},
        headers=guard_auth_headers,
    )
    assert response.status_code == 400
    assert set(response.json().keys()) == {"error", "message"}
