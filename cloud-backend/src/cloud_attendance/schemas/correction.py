from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field

from cloud_attendance.models.correction import CorrectionAction


class CorrectionBase(BaseModel):
    employee_id: str
    attendance_event_id: Optional[str] = None
    action: CorrectionAction
    new_value: dict[str, Any]
    reason: str = Field(..., min_length=1)


class CorrectionCreate(CorrectionBase):
    pass


class Correction(CorrectionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    previous_value: Optional[dict[str, Any]] = None
    performed_by: str
    performed_at: datetime
