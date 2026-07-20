from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from local_attendance.models.facial_reference import FacialReferenceQuality


class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=1)
    employee_number: str | None = None
    department: str | None = None
    job_title: str | None = None
    phone: str | None = None
    notes: str | None = None


class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1)
    employee_number: str | None = None
    department: str | None = None
    job_title: str | None = None
    phone: str | None = None
    notes: str | None = None
    active: bool | None = None


class EmployeeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    employee_number: str
    department: str | None = None
    active: bool
    has_face_reference: bool


class EmployeeDetail(EmployeeSummary):
    job_title: str | None = None
    phone: str | None = None
    notes: str | None = None
    registration_date: date
    created_at: datetime
    updated_at: datetime


class FaceEnrollmentRequest(BaseModel):
    sample_count: int = Field(default=3, ge=1, le=10)


class FaceEnrollmentResponse(BaseModel):
    employee_id: str
    status: FacialReferenceQuality = FacialReferenceQuality.USABLE
    sample_count: int
    enrolled_at: datetime
