from datetime import datetime, timedelta, timezone

from local_attendance.models.attendance_event import AttendanceEvent
from local_attendance.models.verification_attempt import AttendanceType, VerificationAttempt, VerificationResult


def test_duplicate_arrival_blocked_within_window(client, guard_auth_headers, employee_with_face):
    first = client.post(
        "/attendance/verify", json={"employee_id": employee_with_face.id, "type": "arrival"}, headers=guard_auth_headers
    )
    second = client.post(
        "/attendance/verify", json={"employee_id": employee_with_face.id, "type": "arrival"}, headers=guard_auth_headers
    )

    assert first.status_code == 200
    assert first.json()["result"] == "success"
    assert second.status_code == 200
    assert second.json()["result"] == "duplicate_blocked"
    assert second.json()["attendance_event"] is None


def test_duplicate_departure_blocked_within_window(client, guard_auth_headers, employee_with_face):
    client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "departure"},
        headers=guard_auth_headers,
    )
    second = client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "departure"},
        headers=guard_auth_headers,
    )
    assert second.json()["result"] == "duplicate_blocked"


def test_different_type_is_not_blocked_as_duplicate(client, guard_auth_headers, employee_with_face):
    client.post(
        "/attendance/verify", json={"employee_id": employee_with_face.id, "type": "arrival"}, headers=guard_auth_headers
    )
    second = client.post(
        "/attendance/verify",
        json={"employee_id": employee_with_face.id, "type": "departure"},
        headers=guard_auth_headers,
    )
    assert second.json()["result"] == "success"


def test_duplicate_not_blocked_after_window_expires(client, guard_auth_headers, guard_user, employee_with_face, db_session):
    old_time = datetime.now(timezone.utc) - timedelta(seconds=120)
    attempt = VerificationAttempt(
        employee_id=employee_with_face.id,
        guard_id=guard_user.id,
        type_requested=AttendanceType.ARRIVAL,
        timestamp=old_time,
        result=VerificationResult.SUCCESS,
        similarity_score=0.9,
    )
    db_session.add(attempt)
    db_session.commit()
    db_session.refresh(attempt)

    event = AttendanceEvent(
        employee_id=employee_with_face.id,
        type=AttendanceType.ARRIVAL,
        timestamp=old_time,
        guard_id=guard_user.id,
        verification_attempt_id=attempt.id,
    )
    db_session.add(event)
    db_session.commit()
    attempt.attendance_event_id = event.id
    db_session.commit()

    response = client.post(
        "/attendance/verify", json={"employee_id": employee_with_face.id, "type": "arrival"}, headers=guard_auth_headers
    )
    assert response.status_code == 200
    assert response.json()["result"] == "success"
