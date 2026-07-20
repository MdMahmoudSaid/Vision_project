from datetime import datetime

from pydantic import BaseModel, ConfigDict

from local_attendance.models.attendance_event import AttendanceSource
from local_attendance.models.verification_attempt import AttendanceType, VerificationResult


class AttendanceVerifyRequest(BaseModel):
    employee_id: str
    type: AttendanceType


class VerificationAttempt(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    employee_id: str
    guard_id: str
    type_requested: AttendanceType
    timestamp: datetime
    result: VerificationResult
    similarity_score: float | None = None
    failure_reason: str | None = None
    attendance_event_id: str | None = None


class AttendanceEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    employee_id: str
    guard_id: str
    type: AttendanceType
    timestamp: datetime
    verification_attempt_id: str
    source: AttendanceSource


class AttendanceVerifyResponse(BaseModel):
    result: VerificationResult
    message: str | None = None
    verification_attempt: VerificationAttempt
    attendance_event: AttendanceEvent | None = None
