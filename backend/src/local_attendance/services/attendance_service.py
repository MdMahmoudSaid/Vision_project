from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from local_attendance.models.attendance_event import AttendanceEvent
from local_attendance.models.employee import Employee
from local_attendance.models.user import LocalUser
from local_attendance.models.verification_attempt import AttendanceType, VerificationAttempt, VerificationResult


def find_recent_duplicate_event(
    db: Session,
    employee_id: str,
    type_: AttendanceType,
    window_seconds: int,
    now: datetime,
) -> AttendanceEvent | None:
    window_start = now - timedelta(seconds=window_seconds)
    return db.scalar(
        select(AttendanceEvent)
        .where(
            AttendanceEvent.employee_id == employee_id,
            AttendanceEvent.type == type_,
            AttendanceEvent.timestamp >= window_start,
        )
        .order_by(AttendanceEvent.timestamp.desc())
    )


def create_attendance_event(
    db: Session,
    employee: Employee,
    guard: LocalUser,
    type_: AttendanceType,
    attempt: VerificationAttempt,
) -> AttendanceEvent:
    """Create a confirmed attendance event from a successful verification attempt.

    Local-first: the event is written immediately with synced=False; cloud
    synchronization is a later feature and is not required for this write to
    succeed.
    """
    event = AttendanceEvent(
        employee_id=employee.id,
        type=type_,
        guard_id=guard.id,
        verification_attempt_id=attempt.id,
        synced=False,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    attempt.attendance_event_id = event.id
    db.commit()

    return event


@dataclass
class ShiftActivityRecord:
    kind: str
    employee_id: str
    employee_name: str
    type: AttendanceType
    timestamp: datetime
    guard_username: str
    outcome: VerificationResult
    failure_reason: str | None
    attendance_event_id: str | None


def get_shift_activity(db: Session, limit: int = 50) -> list[ShiftActivityRecord]:
    """Combine recent attendance events with failed/duplicate-blocked verification
    attempts into a single, outcome-labeled activity feed.

    Successful attempts are represented only via their linked attendance event so
    each real-world attendance moment appears once, not twice.
    """
    events = db.scalars(select(AttendanceEvent).order_by(AttendanceEvent.timestamp.desc()).limit(limit)).all()

    non_success_attempts = db.scalars(
        select(VerificationAttempt)
        .where(VerificationAttempt.result != VerificationResult.SUCCESS)
        .order_by(VerificationAttempt.timestamp.desc())
        .limit(limit)
    ).all()

    records: list[ShiftActivityRecord] = []

    for event in events:
        records.append(
            ShiftActivityRecord(
                kind="attendance_event",
                employee_id=event.employee_id,
                employee_name=event.employee.full_name,
                type=event.type,
                timestamp=event.timestamp,
                guard_username=event.guard.username,
                outcome=VerificationResult.SUCCESS,
                failure_reason=None,
                attendance_event_id=event.id,
            )
        )

    for attempt in non_success_attempts:
        records.append(
            ShiftActivityRecord(
                kind="verification_attempt",
                employee_id=attempt.employee_id,
                employee_name=attempt.employee.full_name,
                type=attempt.type_requested,
                timestamp=attempt.timestamp,
                guard_username=attempt.guard.username,
                outcome=attempt.result,
                failure_reason=attempt.failure_reason,
                attendance_event_id=None,
            )
        )

    records.sort(key=lambda record: record.timestamp, reverse=True)
    return records[:limit]


@dataclass
class LocalOverviewRecord:
    date: date
    arrivals: int
    departures: int
    failed_attempts: int


def get_local_overview(db: Session, today: date) -> LocalOverviewRecord:
    start = datetime.combine(today, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    arrivals = (
        db.scalar(
            select(func.count()).select_from(AttendanceEvent).where(
                AttendanceEvent.type == AttendanceType.ARRIVAL,
                AttendanceEvent.timestamp >= start,
                AttendanceEvent.timestamp < end,
            )
        )
        or 0
    )
    departures = (
        db.scalar(
            select(func.count()).select_from(AttendanceEvent).where(
                AttendanceEvent.type == AttendanceType.DEPARTURE,
                AttendanceEvent.timestamp >= start,
                AttendanceEvent.timestamp < end,
            )
        )
        or 0
    )
    failed_attempts = (
        db.scalar(
            select(func.count()).select_from(VerificationAttempt).where(
                VerificationAttempt.result == VerificationResult.FAILED,
                VerificationAttempt.timestamp >= start,
                VerificationAttempt.timestamp < end,
            )
        )
        or 0
    )

    return LocalOverviewRecord(date=today, arrivals=arrivals, departures=departures, failed_attempts=failed_attempts)
