from sqlalchemy import func, select
from sqlalchemy.orm import Session

from local_attendance.models.attendance_event import AttendanceEvent
from local_attendance.models.employee import Employee
from local_attendance.models.verification_attempt import VerificationAttempt
from local_attendance.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeNotFoundError(Exception):
    pass


class DuplicateEmployeeNumberError(Exception):
    pass


class InvalidEmployeeDataError(Exception):
    pass


class EmployeeHasHistoryError(Exception):
    """Raised when deleting an employee would destroy attendance/verification
    history. The constitution requires that history be permanent and
    auditable, so this is refused rather than silently cascading — the
    caller should deactivate the employee instead."""

    pass


def _generate_employee_number(db: Session) -> str:
    count = db.scalar(select(func.count()).select_from(Employee)) or 0
    index = count + 1
    while True:
        candidate = f"EMP{index:04d}"
        exists = db.scalar(select(Employee.id).where(Employee.employee_number == candidate))
        if exists is None:
            return candidate
        index += 1


def create_employee(db: Session, payload: EmployeeCreate) -> Employee:
    full_name = payload.full_name.strip()
    if not full_name:
        raise InvalidEmployeeDataError("full_name must not be blank")

    employee_number = payload.employee_number.strip() if payload.employee_number else None
    if employee_number:
        if db.scalar(select(Employee.id).where(Employee.employee_number == employee_number)) is not None:
            raise DuplicateEmployeeNumberError(f"Employee number {employee_number} already exists")
    else:
        employee_number = _generate_employee_number(db)

    employee = Employee(
        full_name=full_name,
        employee_number=employee_number,
        department=payload.department,
        job_title=payload.job_title,
        phone=payload.phone,
        notes=payload.notes,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def get_employee(db: Session, employee_id: str) -> Employee:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise EmployeeNotFoundError(f"Employee {employee_id} not found")
    return employee


def update_employee(db: Session, employee_id: str, payload: EmployeeUpdate) -> Employee:
    employee = get_employee(db, employee_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "full_name" in update_data:
        full_name = (update_data["full_name"] or "").strip()
        if not full_name:
            raise InvalidEmployeeDataError("full_name must not be blank")
        employee.full_name = full_name

    if "employee_number" in update_data:
        new_number = (update_data["employee_number"] or "").strip()
        if new_number and new_number != employee.employee_number:
            if db.scalar(select(Employee.id).where(Employee.employee_number == new_number)) is not None:
                raise DuplicateEmployeeNumberError(f"Employee number {new_number} already exists")
            employee.employee_number = new_number

    for field in ("department", "job_title", "phone", "notes", "active"):
        if field in update_data:
            setattr(employee, field, update_data[field])

    db.commit()
    db.refresh(employee)
    return employee


def delete_employee(db: Session, employee_id: str) -> None:
    employee = get_employee(db, employee_id)

    has_history = db.scalar(
        select(VerificationAttempt.id).where(VerificationAttempt.employee_id == employee_id)
    ) is not None or db.scalar(
        select(AttendanceEvent.id).where(AttendanceEvent.employee_id == employee_id)
    ) is not None

    if has_history:
        raise EmployeeHasHistoryError(
            f"Employee {employee_id} has attendance or verification history and cannot be deleted"
        )

    db.delete(employee)
    db.commit()


def search_employees(
    db: Session,
    query: str | None = None,
    department: str | None = None,
    active: bool | None = True,
) -> list[Employee]:
    stmt = select(Employee)
    if active is not None:
        stmt = stmt.where(Employee.active == active)
    if department:
        stmt = stmt.where(Employee.department == department)
    if query:
        like = f"%{query}%"
        stmt = stmt.where((Employee.full_name.ilike(like)) | (Employee.employee_number.ilike(like)))
    stmt = stmt.order_by(Employee.full_name)
    return list(db.scalars(stmt).all())
