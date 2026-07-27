from sqlalchemy import select
from sqlalchemy.orm import Session

from cloud_attendance.models import SyncIngestLog, SyncedEmployee, SyncedVerificationAttempt, SyncedAttendanceEvent, utcnow
from cloud_attendance.schemas.sync import SyncBatchRequest, SyncBatchResponse


def ingest_sync_batch(db: Session, batch: SyncBatchRequest) -> SyncBatchResponse:
    # Verification attempts and attendance events are immutable once recorded
    # locally, so a plain insert-only-skip-if-exists upsert is correct for
    # them. Employees are NOT immutable — name/department/active status can
    # change after the initial sync (e.g. deactivation) — so an employee row
    # that already exists must be UPDATED, not silently skipped, or those
    # edits would never reach the cloud dashboard (spec FR-001, US1 scenario 4).

    # Process Employees (upsert: update mutable fields if already present)
    employee_ids = {e.id for e in batch.employees}
    existing_employees = {
        e.id: e
        for e in db.scalars(select(SyncedEmployee).where(SyncedEmployee.id.in_(employee_ids)))
    } if employee_ids else {}

    employees_accepted = 0
    for e_schema in batch.employees:
        existing = existing_employees.get(e_schema.id)
        if existing is not None:
            existing.full_name = e_schema.full_name
            existing.employee_number = e_schema.employee_number
            existing.department = e_schema.department
            existing.active = e_schema.active
            existing.has_face_reference = e_schema.has_face_reference
            # synced_at is cloud-owned bookkeeping ("when the cloud last
            # received an update for this employee") — always stamped here,
            # never trusted from the local PC's payload.
            existing.synced_at = utcnow()
        else:
            data = e_schema.model_dump()
            data["synced_at"] = utcnow()
            db.add(SyncedEmployee(**data))
        employees_accepted += 1

    # Process Verification Attempts
    attempt_ids = {a.id for a in batch.verification_attempts}
    existing_attempt_ids = set(
        db.scalars(select(SyncedVerificationAttempt.id).where(SyncedVerificationAttempt.id.in_(attempt_ids)))
    ) if attempt_ids else set()
    
    attempts_accepted = 0
    for a_schema in batch.verification_attempts:
        if a_schema.id not in existing_attempt_ids:
            db.add(SyncedVerificationAttempt(**a_schema.model_dump()))
        attempts_accepted += 1
        
    # Process Attendance Events
    event_ids = {a.id for a in batch.attendance_events}
    existing_event_ids = set(
        db.scalars(select(SyncedAttendanceEvent.id).where(SyncedAttendanceEvent.id.in_(event_ids)))
    ) if event_ids else set()
    
    events_accepted = 0
    for evt_schema in batch.attendance_events:
        if evt_schema.id not in existing_event_ids:
            db.add(SyncedAttendanceEvent(**evt_schema.model_dump()))
        events_accepted += 1
        
    # Log the ingestion
    ingest_log = SyncIngestLog(
        success=True,
        employees_accepted=employees_accepted,
        verification_attempts_accepted=attempts_accepted,
        attendance_events_accepted=events_accepted,
    )
    db.add(ingest_log)
    
    db.commit()
    
    return SyncBatchResponse(
        employees_accepted=employees_accepted,
        verification_attempts_accepted=attempts_accepted,
        attendance_events_accepted=events_accepted,
    )
