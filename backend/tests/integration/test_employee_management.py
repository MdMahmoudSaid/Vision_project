def test_create_employee_generates_employee_number_when_omitted(client, admin_auth_headers):
    response = client.post("/employees", json={"full_name": "Auto Number"}, headers=admin_auth_headers)
    assert response.status_code == 201
    assert response.json()["employee_number"].startswith("EMP")


def test_create_employee_uses_provided_employee_number(client, admin_auth_headers):
    response = client.post(
        "/employees",
        json={"full_name": "Manual Number", "employee_number": "CUSTOM-01"},
        headers=admin_auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["employee_number"] == "CUSTOM-01"


def test_create_employee_rejects_duplicate_employee_number(client, admin_auth_headers):
    client.post("/employees", json={"full_name": "First", "employee_number": "DUP-1"}, headers=admin_auth_headers)
    response = client.post(
        "/employees", json={"full_name": "Second", "employee_number": "DUP-1"}, headers=admin_auth_headers
    )
    assert response.status_code == 409
    assert response.json()["error"] == "duplicate_employee_number"


def test_update_employee_changes_fields(client, admin_auth_headers, employee_with_face):
    response = client.patch(
        f"/employees/{employee_with_face.id}",
        json={"full_name": "Updated Name", "active": False},
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"
    assert response.json()["active"] is False


def test_update_employee_marks_synced_false_for_resync(client, admin_auth_headers, employee_with_face, db_session):
    # Simulate the employee having already synced to the cloud once.
    employee_with_face.synced = True
    db_session.commit()

    response = client.patch(
        f"/employees/{employee_with_face.id}",
        json={"department": "New Department"},
        headers=admin_auth_headers,
    )
    assert response.status_code == 200

    db_session.refresh(employee_with_face)
    assert employee_with_face.synced is False


def test_update_employee_not_found_returns_404(client, admin_auth_headers):
    response = client.patch(
        "/employees/00000000-0000-0000-0000-000000000000",
        json={"full_name": "X"},
        headers=admin_auth_headers,
    )
    assert response.status_code == 404


def test_search_employees_filters_by_query(client, admin_auth_headers, guard_auth_headers):
    client.post("/employees", json={"full_name": "Alice Alpha"}, headers=admin_auth_headers)
    client.post("/employees", json={"full_name": "Bob Beta"}, headers=admin_auth_headers)

    response = client.get("/employees", params={"query": "Alice"}, headers=guard_auth_headers)
    assert response.status_code == 200
    names = [item["full_name"] for item in response.json()]
    assert names == ["Alice Alpha"]


def test_search_employees_excludes_inactive_by_default(client, admin_auth_headers, guard_auth_headers):
    created = client.post("/employees", json={"full_name": "Inactive Person"}, headers=admin_auth_headers).json()
    client.patch(f"/employees/{created['id']}", json={"active": False}, headers=admin_auth_headers)

    response = client.get("/employees", headers=guard_auth_headers)
    assert response.status_code == 200
    assert created["id"] not in [item["id"] for item in response.json()]
