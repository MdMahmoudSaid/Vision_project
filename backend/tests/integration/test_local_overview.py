def test_local_overview_counts_arrivals_departures_and_failed_attempts(
    client, guard_auth_headers, employee_with_face, fake_face_engine
):
    client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )
    client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "departure"},
        headers=guard_auth_headers,
    )

    fake_face_engine.compare_is_match = False
    client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )

    response = client.get("/dashboard/overview", headers=guard_auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["arrivals"] == 1
    assert body["departures"] == 1
    assert body["failed_attempts"] == 1


def test_local_overview_zero_counts_when_no_activity(client, guard_auth_headers):
    response = client.get("/dashboard/overview", headers=guard_auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["arrivals"] == 0
    assert body["departures"] == 0
    assert body["failed_attempts"] == 0


def test_local_overview_excludes_duplicate_blocked_from_failed_count(client, guard_auth_headers, employee_with_face):
    client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )
    duplicate = client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )
    assert duplicate.json()["result"] == "duplicate_blocked"

    response = client.get("/dashboard/overview", headers=guard_auth_headers)
    assert response.json()["failed_attempts"] == 0
