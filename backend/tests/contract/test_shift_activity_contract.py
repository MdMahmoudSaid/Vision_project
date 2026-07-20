def test_shift_activity_contract_shape(client, guard_auth_headers, employee_with_face):
    client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )

    response = client.get("/attendance/shift-activity", headers=guard_auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1
    item = body[0]
    assert {
        "kind",
        "employee_id",
        "employee_name",
        "type",
        "timestamp",
        "guard_username",
        "outcome",
        "failure_reason",
        "attendance_event_id",
    }.issubset(item.keys())


def test_shift_activity_rejects_limit_out_of_range(client, guard_auth_headers):
    response = client.get("/attendance/shift-activity", params={"limit": 500}, headers=guard_auth_headers)
    assert response.status_code == 422


def test_dashboard_overview_contract_shape(client, guard_auth_headers):
    response = client.get("/dashboard/overview", headers=guard_auth_headers)
    assert response.status_code == 200
    assert set(response.json().keys()) == {"date", "arrivals", "departures", "failed_attempts"}
