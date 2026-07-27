from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class SyncedEmployee(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    full_name: str
    employee_number: str
    department: Optional[str] = None
    active: bool
    has_face_reference: bool
    synced_at: datetime


class SyncedVerificationAttempt(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    employee_id: str
    type_requested: str
    timestamp: datetime
    result: str
    similarity_score: Optional[float] = None
    failure_reason: Optional[str] = None
    attendance_event_id: Optional[str] = None


class SyncedAttendanceEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    employee_id: str
    type: str
    timestamp: datetime
    verification_attempt_id: str


class SyncBatchRequest(BaseModel):
    employees: List[SyncedEmployee]
    verification_attempts: List[SyncedVerificationAttempt]
    attendance_events: List[SyncedAttendanceEvent]


class SyncBatchResponse(BaseModel):
    employees_accepted: int
    verification_attempts_accepted: int
    attendance_events_accepted: int
