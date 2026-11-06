from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.attendance import get_current_user, get_db
from app.models.disciplinary import DisciplinaryCase
from app.models.employee import Employee
from app.models.user import User

router = APIRouter()
HR_ROLES = {"HR", "HR_ADMIN"}


class DisciplinaryCaseCreate(BaseModel):
    employee_id: UUID
    incident_date: date
    description: str = Field(min_length=1, max_length=500)
    action_taken: Optional[str] = Field(default=None, max_length=255)


class DisciplinaryCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    incident_date: date
    description: str
    action_taken: Optional[str]
    status: str


def require_hr(user: User) -> None:
    if user.role.upper() not in HR_ROLES:
        raise HTTPException(status_code=403, detail="Only HR can manage disciplinary cases")


@router.post("/", response_model=DisciplinaryCaseResponse, status_code=201)
def create_case(
    request: DisciplinaryCaseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    if db.query(Employee.id).filter(Employee.id == request.employee_id).first() is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    case = DisciplinaryCase(
        employee_id=request.employee_id,
        incident_date=request.incident_date,
        description=request.description.strip(),
        action_taken=request.action_taken.strip() if request.action_taken else None,
        status="OPEN",
    )
    if not case.description:
        raise HTTPException(status_code=422, detail="Description cannot be blank")
    db.add(case)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(case)
    return case


@router.get("/", response_model=list[DisciplinaryCaseResponse])
def list_cases(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    return db.query(DisciplinaryCase).order_by(DisciplinaryCase.incident_date.desc()).all()
