from datetime import date, datetime

from pydantic import BaseModel

from local_attendance.models.verification_attempt import AttendanceType, VerificationResult


class ShiftActivityItem(BaseModel):
    kind: str
    employee_id: str
    employee_name: str
    type: AttendanceType | None = None
    timestamp: datetime
    guard_username: str | None = None
    outcome: VerificationResult
    failure_reason: str | None = None
    attendance_event_id: str | None = None


class LocalOverview(BaseModel):
    date: date
    arrivals: int
    departures: int
    failed_attempts: int
