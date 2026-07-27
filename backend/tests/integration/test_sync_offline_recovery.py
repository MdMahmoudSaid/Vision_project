"""US1 (spec.md Acceptance Scenario 2 / quickstart.md Scenario 1): events
recorded while the local PC's sync target is unreachable must still be
delivered exactly once after connectivity returns — no manual intervention,
no duplicates, no losses."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy.orm import Session

from local_attendance.models.attendance_event import AttendanceEvent
from local_attendance.models.employee import Employee
from local_attendance.models.user import LocalUser
from local_attendance.models.verification_attempt import AttendanceType, VerificationAttempt, VerificationResult
from local_attendance.sync.client import run_sync_batch


def _record_offline_attendance(db_session: Session, guard: LocalUser) -> tuple[Employee, VerificationAttempt, AttendanceEvent]:
    employee = Employee(full_name="Offline Gap Employee", employee_number="OFF-001", synced=False)
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    attempt = VerificationAttempt(
        employee_id=employee.id,
        guard_id=guard.id,
        type_requested=AttendanceType.ARRIVAL,
        result=VerificationResult.SUCCESS,
        synced=False,
    )
    db_session.add(attempt)
    db_session.flush()

    event = AttendanceEvent(
        employee_id=employee.id,
        type=AttendanceType.ARRIVAL,
        guard_id=guard.id,
        verification_attempt_id=attempt.id,
        synced=False,
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(attempt)
    db_session.refresh(event)
    return employee, attempt, event


@pytest.mark.anyio
async def test_offline_gap_then_recovery_delivers_records_exactly_once(db_session: Session, admin_user):
    employee, attempt, event = _record_offline_attendance(db_session, admin_user)

    # --- Simulate the sync target being unreachable (the "offline gap") ---
    with patch("local_attendance.sync.client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = httpx.ConnectError("connection refused")

        succeeded = await run_sync_batch(db_session)
        assert succeeded is False

    db_session.refresh(employee)
    db_session.refresh(attempt)
    db_session.refresh(event)
    assert employee.synced is False
    assert attempt.synced is False
    assert event.synced is False

    # --- Connectivity restored: the same records must now go through ---
    with patch("local_attendance.sync.client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = AsyncMock(status_code=200)

        succeeded = await run_sync_batch(db_session)
        assert succeeded is True

        call_args = mock_client.post.call_args[1]
        payload = call_args["json"]
        assert [e["id"] for e in payload["employees"]] == [employee.id]
        assert [a["id"] for a in payload["verification_attempts"]] == [attempt.id]
        assert [e["id"] for e in payload["attendance_events"]] == [event.id]

    db_session.refresh(employee)
    db_session.refresh(attempt)
    db_session.refresh(event)
    assert employee.synced is True
    assert attempt.synced is True
    assert event.synced is True

    # --- A subsequent sync tick must not re-send already-synced records ---
    with patch("local_attendance.sync.client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = AsyncMock(status_code=200)

        succeeded = await run_sync_batch(db_session)
        assert succeeded is True
        mock_client.post.assert_not_called()
