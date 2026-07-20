def test_shift_activity_orders_most_recent_first(client, guard_auth_headers, employee_with_face, fake_face_engine):
    client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )

    fake_face_engine.compare_is_match = False
    client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "departure"},
        headers=guard_auth_headers,
    )

    response = client.get("/attendance/shift-activity", headers=guard_auth_headers)
    body = response.json()
    assert len(body) == 2
    timestamps = [item["timestamp"] for item in body]
    assert timestamps == sorted(timestamps, reverse=True)
    assert body[0]["outcome"] == "failed"
    assert body[1]["outcome"] == "success"


def test_shift_activity_respects_limit_parameter(client, guard_auth_headers, employee_with_face):
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

    response = client.get("/attendance/shift-activity", params={"limit": 1}, headers=guard_auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_shift_activity_labels_success_failure_and_duplicate_outcomes(
    client, guard_auth_headers, employee_with_face, fake_face_engine
):
    # success
    client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )
    # duplicate_blocked (same employee/type again)
    client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )
    # failed (different type so it's not blocked as duplicate)
    fake_face_engine.compare_is_match = False
    client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "departure"},
        headers=guard_auth_headers,
    )

    response = client.get("/attendance/shift-activity", headers=guard_auth_headers)
    outcomes = {item["outcome"] for item in response.json()}
    assert outcomes == {"success", "duplicate_blocked", "failed"}

    success_items = [item for item in response.json() if item["outcome"] == "success"]
    assert success_items[0]["kind"] == "attendance_event"
    assert success_items[0]["attendance_event_id"] is not None

    non_success_items = [item for item in response.json() if item["outcome"] != "success"]
    assert all(item["kind"] == "verification_attempt" for item in non_success_items)
    assert all(item["attendance_event_id"] is None for item in non_success_items)
