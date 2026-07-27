import enum
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class CompletenessStatus(str, enum.Enum):
    COMPLETE = "complete"
    MISSING_DEPARTURE = "missing_departure"
    MISSING_ARRIVAL = "missing_arrival"
    NO_RECORD = "no_record"


class ReportScopeType(str, enum.Enum):
    EMPLOYEE = "employee"
    ORGANIZATION = "organization"


class ReportScope(BaseModel):
    type: ReportScopeType
    employee_id: Optional[str] = None


class ReportGranularity(str, enum.Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    CUSTOM = "custom"


class ReportPeriod(BaseModel):
    granularity: ReportGranularity
    date_from: date
    date_to: date


class ReportRow(BaseModel):
    employee_id: str
    employee_name: str
    date: date
    arrival_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    worked_duration_minutes: Optional[int] = None
    completeness: CompletenessStatus
    corrected: bool = False


class Report(BaseModel):
    scope: ReportScope
    period: ReportPeriod
    rows: List[ReportRow]
    generated_at: datetime
    may_be_incomplete: bool
