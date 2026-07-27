from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from cloud_attendance.auth.dependencies import require_any_cloud_role
from cloud_attendance.database import get_db
from cloud_attendance.models.cloud_user import CloudUser
from cloud_attendance.models.synced_employee import SyncedEmployee as SyncedEmployeeModel
from cloud_attendance.schemas.employee import EmployeeAttendanceHistory
from cloud_attendance.schemas.report import ReportGranularity
from cloud_attendance.schemas.sync import SyncedEmployee as SyncedEmployeeSchema
from cloud_attendance.services.report_service import generate_report

router = APIRouter(prefix="/employees", tags=["employees"])

_DEFAULT_HISTORY_WINDOW_DAYS = 30


@router.get("", response_model=list[SyncedEmployeeSchema])
def list_employees(
    query: str | None = None,
    department: str | None = None,
    active: bool | None = True,
    db: Session = Depends(get_db),
    _: CloudUser = Depends(require_any_cloud_role),
) -> list[SyncedEmployeeModel]:
    stmt = select(SyncedEmployeeModel)
    if active is not None:
        stmt = stmt.where(SyncedEmployeeModel.active == active)
    if department:
        stmt = stmt.where(SyncedEmployeeModel.department == department)
    if query:
        like = f"%{query}%"
        stmt = stmt.where(
            (SyncedEmployeeModel.full_name.ilike(like)) | (SyncedEmployeeModel.employee_number.ilike(like))
        )
    stmt = stmt.order_by(SyncedEmployeeModel.full_name)
    return list(db.scalars(stmt).all())


@router.get("/{employee_id}/attendance", response_model=EmployeeAttendanceHistory)
def get_employee_attendance_history(
    employee_id: str,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    _: CloudUser = Depends(require_any_cloud_role),
) -> EmployeeAttendanceHistory:
    employee = db.get(SyncedEmployeeModel, employee_id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "employee_not_found", "message": f"Employee {employee_id} not found"},
        )

    resolved_date_to = date_to or date.today()
    resolved_date_from = date_from or (resolved_date_to - timedelta(days=_DEFAULT_HISTORY_WINDOW_DAYS))

    report = generate_report(db, ReportGranularity.CUSTOM, resolved_date_from, resolved_date_to, employee_id)
    return EmployeeAttendanceHistory(
        employee_id=employee.id,
        employee_name=employee.full_name,
        may_be_incomplete=report.may_be_incomplete,
        days=report.rows,
    )
