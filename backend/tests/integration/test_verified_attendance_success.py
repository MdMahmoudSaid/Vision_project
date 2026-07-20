def test_successful_arrival_creates_attempt_and_event(client, guard_auth_headers, employee_with_face):
    response = client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["result"] == "success"
    assert body["verification_attempt"]["type_requested"] == "arrival"
    assert body["attendance_event"]["type"] == "arrival"
    assert body["verification_attempt"]["attendance_event_id"] == body["attendance_event"]["id"]


def test_successful_departure_creates_separate_event(client, guard_auth_headers, employee_with_face):
    arrival = client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )
    departure = client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "departure"},
        headers=guard_auth_headers,
    )

    assert arrival.status_code == 200
    assert departure.status_code == 200
    assert departure.json()["result"] == "success"
    assert departure.json()["attendance_event"]["type"] == "departure"
    assert arrival.json()["attendance_event"]["id"] != departure.json()["attendance_event"]["id"]
