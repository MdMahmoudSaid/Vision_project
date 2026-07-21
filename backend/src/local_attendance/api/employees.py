from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from local_attendance.auth.dependencies import require_admin, require_guard_or_admin
from local_attendance.camera.base import CameraBase, get_camera
from local_attendance.database import get_db
from local_attendance.face.engine import FaceEngineBase, get_face_engine
from local_attendance.models.employee import Employee
from local_attendance.models.facial_reference import FacialReference, FacialReferenceQuality
from local_attendance.models.user import LocalUser
from local_attendance.schemas.employee import (
    EmployeeCreate,
    EmployeeDetail,
    EmployeeSummary,
    EmployeeUpdate,
    FaceEnrollmentRequest,
    FaceEnrollmentResponse,
)
from local_attendance.services import employee_service
from local_attendance.services.face_enrollment_service import FaceEnrollmentUnusableError, enroll_face

router = APIRouter(prefix="/employees", tags=["employees"])


def _has_face_reference(db: Session, employee_id: str) -> bool:
    return (
        db.scalar(
            select(FacialReference.id).where(
                FacialReference.employee_id == employee_id,
                FacialReference.quality_status == FacialReferenceQuality.USABLE,
                FacialReference.replaced_at.is_(None),
            )
        )
        is not None
    )


def _to_summary(db: Session, employee: Employee) -> EmployeeSummary:
    return EmployeeSummary(
        id=employee.id,
        full_name=employee.full_name,
        employee_number=employee.employee_number,
        department=employee.department,
        active=employee.active,
        has_face_reference=_has_face_reference(db, employee.id),
    )


def _to_detail(db: Session, employee: Employee) -> EmployeeDetail:
    summary = _to_summary(db, employee)
    return EmployeeDetail(
        **summary.model_dump(),
        job_title=employee.job_title,
        phone=employee.phone,
        notes=employee.notes,
        registration_date=employee.registration_date,
        created_at=employee.created_at,
        updated_at=employee.updated_at,
    )


@router.get("", response_model=list[EmployeeSummary])
def list_employees(
    query: str | None = None,
    department: str | None = None,
    active: bool | None = True,
    db: Session = Depends(get_db),
    _: LocalUser = Depends(require_guard_or_admin),
) -> list[EmployeeSummary]:
    employees = employee_service.search_employees(db, query=query, department=department, active=active)
    return [_to_summary(db, employee) for employee in employees]


@router.post("", response_model=EmployeeDetail, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    _: LocalUser = Depends(require_admin),
) -> EmployeeDetail:
    try:
        employee = employee_service.create_employee(db, payload)
    except employee_service.DuplicateEmployeeNumberError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "duplicate_employee_number", "message": str(exc)},
        ) from exc
    except employee_service.InvalidEmployeeDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_employee_data", "message": str(exc)},
        ) from exc
    return _to_detail(db, employee)


@router.patch("/{employee_id}", response_model=EmployeeDetail)
def update_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    _: LocalUser = Depends(require_admin),
) -> EmployeeDetail:
    try:
        employee = employee_service.update_employee(db, employee_id, payload)
    except employee_service.EmployeeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "employee_not_found", "message": str(exc)},
        ) from exc
    except employee_service.DuplicateEmployeeNumberError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "duplicate_employee_number", "message": str(exc)},
        ) from exc
    except employee_service.InvalidEmployeeDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_employee_data", "message": str(exc)},
        ) from exc
    return _to_detail(db, employee)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: str,
    db: Session = Depends(get_db),
    _: LocalUser = Depends(require_admin),
) -> None:
    try:
        employee_service.delete_employee(db, employee_id)
    except employee_service.EmployeeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "employee_not_found", "message": str(exc)},
        ) from exc
    except employee_service.EmployeeHasHistoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "employee_has_history",
                "message": "This employee has attendance history and cannot be deleted. Deactivate them instead.",
            },
        ) from exc


@router.post("/{employee_id}/face", response_model=FaceEnrollmentResponse)
def enroll_employee_face(
    employee_id: str,
    payload: FaceEnrollmentRequest | None = None,
    db: Session = Depends(get_db),
    admin: LocalUser = Depends(require_admin),
    camera: CameraBase = Depends(get_camera),
    face_engine: FaceEngineBase = Depends(get_face_engine),
) -> FaceEnrollmentResponse:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "employee_not_found", "message": f"Employee {employee_id} not found"},
        )

    sample_count = payload.sample_count if payload else 3

    try:
        reference = enroll_face(db, employee, admin, camera, face_engine, sample_count=sample_count)
    except FaceEnrollmentUnusableError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "capture_unusable", "message": str(exc)},
        ) from exc

    return FaceEnrollmentResponse(
        employee_id=employee.id,
        status=FacialReferenceQuality.USABLE,
        sample_count=reference.sample_count,
        enrolled_at=reference.created_at,
    )
