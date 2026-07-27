from typing import List

from pydantic import BaseModel

from cloud_attendance.schemas.report import ReportRow


class EmployeeAttendanceHistory(BaseModel):
    employee_id: str
    employee_name: str
    may_be_incomplete: bool
    days: List[ReportRow]
