def test_failed_verification_creates_failed_attempt_and_no_event(
    client, guard_auth_headers, employee_with_face, fake_face_engine
):
    fake_face_engine.compare_is_match = False

    response = client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"] == "failed"
    assert body["attendance_event"] is None
    assert body["verification_attempt"]["result"] == "failed"
    assert body["verification_attempt"]["failure_reason"] == "face_mismatch"
    assert body["verification_attempt"]["attendance_event_id"] is None
