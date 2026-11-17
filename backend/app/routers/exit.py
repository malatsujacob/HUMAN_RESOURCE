from datetime import date, datetime, timezone
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.routers.attendance import get_current_user, get_db
from app.models.employee import Employee
from app.models.exit import EmployeeExit
from app.models.user import User

router = APIRouter()
HR_ROLES = {"HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"}


class ExitCreate(BaseModel):
    employee_id: UUID
    last_working_day: date
    reason: str = Field(min_length=1, max_length=500)

class ClearanceReview(BaseModel):
    clearance_status: Literal["IN_PROGRESS", "CLEARED", "BLOCKED"]
    note: str = Field(min_length=5, max_length=1000)


class ExitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    last_working_day: date
    reason: str
    clearance_status: str
    clearance_note: Optional[str] = None
    clearance_reviewed_by: Optional[UUID] = None
    clearance_reviewed_at: Optional[datetime] = None


def require_hr(user: User) -> None:
    if user.role.upper() not in HR_ROLES:
        raise HTTPException(status_code=403, detail="Only HR can manage employee exits")


@router.post("/", response_model=ExitResponse, status_code=201)
def initiate_exit(
    request: ExitCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    employee = db.query(Employee).filter(Employee.id == request.employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee_exit = EmployeeExit(
        employee_id=employee.id,
        last_working_day=request.last_working_day,
        reason=request.reason.strip(),
        clearance_status="PENDING",
    )
    if not employee_exit.reason:
        raise HTTPException(status_code=422, detail="Reason cannot be blank")
    db.add(employee_exit)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(employee_exit)
    return employee_exit


@router.get("/", response_model=list[ExitResponse])
def list_exits(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    return db.query(EmployeeExit).order_by(EmployeeExit.last_working_day.desc()).all()


@router.put("/{exit_id}/clearance", response_model=ExitResponse)
def review_clearance(
    exit_id: UUID,
    request: ClearanceReview,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    employee_exit = db.query(EmployeeExit).filter(EmployeeExit.id == exit_id).with_for_update().first()
    if employee_exit is None:
        raise HTTPException(status_code=404, detail="Employee exit record not found.")
    if employee_exit.clearance_status == "CLEARED":
        raise HTTPException(status_code=409, detail="This employee's clearance has already been completed.")
    employee_exit.clearance_status = request.clearance_status
    employee_exit.clearance_note = request.note.strip()
    if not employee_exit.clearance_note:
        raise HTTPException(status_code=422, detail="Clearance note cannot be blank.")
    employee_exit.clearance_reviewed_by = user.id
    employee_exit.clearance_reviewed_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(employee_exit)
    return employee_exit
