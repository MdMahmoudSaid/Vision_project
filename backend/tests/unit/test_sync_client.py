from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.orm import Session

from local_attendance.models.employee import Employee
from local_attendance.models.facial_reference import FacialReference, FacialReferenceQuality
from local_attendance.sync.client import run_sync_batch


@pytest.mark.anyio
async def test_run_sync_batch_success(db_session: Session, admin_user):
    # Setup some unsynced data
    emp1 = Employee(full_name="Emp 1", employee_number="E001", synced=False)
    emp2 = Employee(full_name="Emp 2", employee_number="E002", synced=True)
    db_session.add(emp1)
    db_session.add(emp2)
    db_session.commit()

    with patch("local_attendance.sync.client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = AsyncMock(status_code=200)

        # Run sync
        await run_sync_batch(db_session)

        # emp1 should be synced=True now, emp2 remains True
        db_session.refresh(emp1)
        db_session.refresh(emp2)
        assert emp1.synced is True
        assert emp2.synced is True

        # Ensure post was called
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args[1]
        payload = call_args["json"]
        assert len(payload["employees"]) == 1
        assert payload["employees"][0]["id"] == emp1.id


@pytest.mark.anyio
async def test_run_sync_batch_failure(db_session: Session, admin_user):
    emp1 = Employee(full_name="Emp 1", employee_number="E001", synced=False)
    db_session.add(emp1)
    db_session.commit()

    with patch("local_attendance.sync.client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        # Return 500
        mock_client.post.return_value = AsyncMock(status_code=500)

        # Run sync
        await run_sync_batch(db_session)

        # Should still be False
        db_session.refresh(emp1)
        assert emp1.synced is False


@pytest.mark.anyio
async def test_run_sync_batch_reports_only_usable_face_reference(db_session: Session, admin_user):
    """A rejected or replaced facial reference must not report
    has_face_reference=True — only a USABLE, non-replaced one counts,
    matching local_attendance/api/employees.py's own definition."""
    emp = Employee(full_name="Rejected Ref", employee_number="E010", synced=False)
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)

    rejected_ref = FacialReference(
        employee_id=emp.id,
        embedding="[]",
        sample_count=1,
        quality_status=FacialReferenceQuality.REJECTED,
        created_by_user_id=admin_user.id,
    )
    db_session.add(rejected_ref)
    db_session.commit()

    with patch("local_attendance.sync.client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = AsyncMock(status_code=200)

        await run_sync_batch(db_session)

        call_args = mock_client.post.call_args[1]
        payload = call_args["json"]
        assert payload["employees"][0]["has_face_reference"] is False
