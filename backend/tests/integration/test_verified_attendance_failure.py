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


def test_spoofed_capture_is_rejected_with_distinct_reason(
    client, db_session, guard_auth_headers, employee_with_face, fake_face_engine
):
    fake_face_engine.raise_on_compare = True
    fake_face_engine.raise_reason = "spoof_detected"

    response = client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "arrival"},
        headers=guard_auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["error"] == "spoof_detected"

    from local_attendance.models.verification_attempt import VerificationAttempt

    attempt = db_session.query(VerificationAttempt).filter_by(employee_id=employee_with_face.id).one()
    assert attempt.failure_reason == "spoof_detected"
