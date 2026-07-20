from local_attendance.models.attendance_event import AttendanceEvent
from local_attendance.models.verification_attempt import VerificationAttempt, VerificationResult


def test_duplicate_blocked_creates_attempt_without_event(client, guard_auth_headers, employee_with_face, db_session):
    client.post(
        "/attendance/verify", json={"employee_id": employee_with_face.id, "type": "arrival"}, headers=guard_auth_headers
    )
    client.post(
        "/attendance/verify", json={"employee_id": employee_with_face.id, "type": "arrival"}, headers=guard_auth_headers
    )

    attempts = db_session.query(VerificationAttempt).filter_by(employee_id=employee_with_face.id).all()
    events = db_session.query(AttendanceEvent).filter_by(employee_id=employee_with_face.id).all()

    assert len(attempts) == 2
    assert len(events) == 1

    duplicate_attempts = [a for a in attempts if a.result == VerificationResult.DUPLICATE_BLOCKED]
    assert len(duplicate_attempts) == 1
    assert duplicate_attempts[0].attendance_event_id is None
    assert duplicate_attempts[0].failure_reason == "duplicate_recent_attendance"
