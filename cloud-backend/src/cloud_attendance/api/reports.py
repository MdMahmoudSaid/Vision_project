from datetime import date, datetime, timedelta
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from cloud_attendance.auth.dependencies import require_any_cloud_role
from cloud_attendance.database import get_db
from cloud_attendance.models.cloud_user import CloudUser
from cloud_attendance.schemas.report import Report, ReportGranularity
from cloud_attendance.services.report_service import generate_report
from cloud_attendance.services.export_service import generate_pdf_export, generate_excel_export

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

def parse_date(date_str: str) -> date:
    try:
        return date.fromisoformat(date_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_date", "message": f"Invalid date format: {date_str}. Must be YYYY-MM-DD"}
        ) from exc

def parse_month(month_str: str) -> tuple[date, date]:
    try:
        # month_str is YYYY-MM
        year_str, month_str = month_str.split("-")
        y = int(year_str)
        m = int(month_str)
        start = date(y, m, 1)
        if m == 12:
            end = date(y + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(y, m + 1, 1) - timedelta(days=1)
        return start, end
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_month", "message": "Invalid month format. Must be YYYY-MM"}
        ) from exc

@router.get("/daily", response_model=Report)
def get_daily_report(
    date: str = Query(..., description="Date YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: CloudUser = Depends(require_any_cloud_role)
) -> Report:
    parsed_date = parse_date(date)
    return generate_report(db, ReportGranularity.DAY, parsed_date, parsed_date)

@router.get("/weekly", response_model=Report)
def get_weekly_report(
    week_start: str = Query(..., description="Week start date YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: CloudUser = Depends(require_any_cloud_role)
) -> Report:
    start_date = parse_date(week_start)
    end_date = start_date + timedelta(days=6)
    return generate_report(db, ReportGranularity.WEEK, start_date, end_date)

@router.get("/monthly", response_model=Report)
def get_monthly_report(
    month: str = Query(..., description="Month YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: CloudUser = Depends(require_any_cloud_role)
) -> Report:
    start_date, end_date = parse_month(month)
    return generate_report(db, ReportGranularity.MONTH, start_date, end_date)

@router.get("/custom", response_model=Report)
def get_custom_report(
    date_from: str = Query(..., description="Start date YYYY-MM-DD"),
    date_to: str = Query(..., description="End date YYYY-MM-DD"),
    employee_id: Optional[str] = Query(None, description="Scope to a single employee"),
    db: Session = Depends(get_db),
    current_user: CloudUser = Depends(require_any_cloud_role)
) -> Report:
    start_date = parse_date(date_from)
    end_date = parse_date(date_to)
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_range", "message": "date_from must be before or equal to date_to"}
        )
    return generate_report(db, ReportGranularity.CUSTOM, start_date, end_date, employee_id)

@router.get("/export")
def export_report(
    type: str = Query(..., pattern="^(daily|weekly|monthly|custom)$"),
    format: str = Query(..., pattern="^(pdf|xlsx)$"),
    date: Optional[str] = Query(None),
    week_start: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    employee_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: CloudUser = Depends(require_any_cloud_role)
) -> Response:
    # Resolve the report
    if type == "daily":
        if not date:
            raise HTTPException(status_code=400, detail={"error": "missing_param", "message": "date is required for daily report"})
        parsed_date = parse_date(date)
        report = generate_report(db, ReportGranularity.DAY, parsed_date, parsed_date)
    elif type == "weekly":
        if not week_start:
            raise HTTPException(status_code=400, detail={"error": "missing_param", "message": "week_start is required for weekly report"})
        start_date = parse_date(week_start)
        end_date = start_date + timedelta(days=6)
        report = generate_report(db, ReportGranularity.WEEK, start_date, end_date)
    elif type == "monthly":
        if not month:
            raise HTTPException(status_code=400, detail={"error": "missing_param", "message": "month is required for monthly report"})
        start_date, end_date = parse_month(month)
        report = generate_report(db, ReportGranularity.MONTH, start_date, end_date)
    else: # custom
        if not date_from or not date_to:
            raise HTTPException(status_code=400, detail={"error": "missing_param", "message": "date_from and date_to are required for custom report"})
        start_date = parse_date(date_from)
        end_date = parse_date(date_to)
        report = generate_report(db, ReportGranularity.CUSTOM, start_date, end_date, employee_id)

    if format == "pdf":
        pdf_bytes = generate_pdf_export(report)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=report_{type}.pdf"}
        )
    else: # xlsx
        xlsx_bytes = generate_excel_export(report)
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=report_{type}.xlsx"}
        )
