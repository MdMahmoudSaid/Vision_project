def test_guard_cannot_create_employee(client, guard_auth_headers):
    response = client.post("/employees", json={"full_name": "Blocked"}, headers=guard_auth_headers)
    assert response.status_code == 403
    assert response.json()["error"] == "forbidden"


def test_guard_cannot_update_employee(client, guard_auth_headers, employee_with_face):
    response = client.patch(
        f"/employees/{employee_with_face.id}", json={"department": "X"}, headers=guard_auth_headers
    )
    assert response.status_code == 403


def test_guard_cannot_enroll_face(client, guard_auth_headers, employee_with_face):
    response = client.post(f"/employees/{employee_with_face.id}/face", headers=guard_auth_headers)
    assert response.status_code == 403


def test_admin_can_create_employee_and_enroll_face(client, admin_auth_headers):
    create_response = client.post("/employees", json={"full_name": "Allowed"}, headers=admin_auth_headers)
    assert create_response.status_code == 201

    face_response = client.post(
        f"/employees/{create_response.json()['id']}/face", headers=admin_auth_headers
    )
    assert face_response.status_code == 200


def test_unauthenticated_request_is_denied_before_reaching_service(client):
    response = client.post("/employees", json={"full_name": "No Token"})
    assert response.status_code == 401
