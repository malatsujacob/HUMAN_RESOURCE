from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.attendance import get_current_user, get_db
from app.models.employee import Employee
from app.models.exit import EmployeeExit
from app.models.user import User

router = APIRouter()
HR_ROLES = {"HR", "HR_ADMIN"}


class ExitCreate(BaseModel):
    employee_id: UUID
    last_working_day: date
    reason: str = Field(min_length=1, max_length=500)


class ExitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    last_working_day: date
    reason: str
    clearance_status: str


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
